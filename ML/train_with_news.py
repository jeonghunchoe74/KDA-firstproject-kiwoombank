import os
import time
import argparse
import html
import requests

from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

from transformers import pipeline
from openai import OpenAI

# =========================
# 설정(필요 시 값만 조정)
# =========================
COMPANY_COL = "company_name"     # 회사명 열 이름
TARGET_COL = "credit_ratings"             # 타깃(신용등급) 열 이름
NEWS_PER_PAGE = 50
MAX_PAGES = 2
REQUEST_TIMEOUT = 10
SLEEP_BETWEEN_CALLS = 0.2

# 최근성 가중치(반감기: 일 단위)
RECENCY_HALF_LIFE_DAYS = 15

# 매체 가중치(도메인 → 가중치)
SOURCE_WEIGHT = {
    "www.hankyung.com": 1.2,
    "www.yonhapnews.co.kr": 1.2,
    "www.mk.co.kr": 1.1,
}

# OpenAI 번역 모델
OPENAI_TRANSLATE_MODEL = "gpt-4o-mini"
OPENAI_TRANSLATE_TEMPERATURE = 0.0
OPENAI_TRANSLATE_BATCH = 20

# FinBERT 영어 금융 감성 모델(3클래스)
FINBERT_MODEL = "yiyanghkust/finbert-tone"  # .bin 체크포인트 → torch 2.6+ 필요


# =========================
# 유틸
# =========================
def clean_text(t: str) -> str:
    if not t:
        return ""
    t = t.replace("<b>", "").replace("</b>", "")
    t = html.unescape(t)
    return t.strip()

def parse_pubdate(pubdate_str: str) -> datetime:
    # Naver pubDate 예시: 'Mon, 23 Sep 2024 10:30:00 +0900'
    try:
        return datetime.strptime(pubdate_str, "%a, %d %b %Y %H:%M:%S %z")
    except Exception:
        return datetime.now(timezone.utc)

def recency_weight(pub_dt: datetime, now: datetime) -> float:
    delta_days = max(0.0, (now - pub_dt).total_seconds() / 86400.0)
    return 0.5 ** (delta_days / float(RECENCY_HALF_LIFE_DAYS))

def source_weight(host: str) -> float:
    return SOURCE_WEIGHT.get(host, 1.0)

def dedup_by_title_host(items: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for it in items:
        title = clean_text(it.get("title", ""))
        host = urlparse(it.get("link", "")).netloc
        key = (title, host)
        if key in seen:
            continue
        seen.add(key)
        it["_clean_title"] = title
        it["_host"] = host
        out.append(it)
    return out

def build_inputs(items: List[Dict]) -> Tuple[List[str], List[float]]:
    now = datetime.now(timezone.utc)
    texts, weights = [], []
    for it in items:
        title = clean_text(it.get("title", ""))
        desc  = clean_text(it.get("description", ""))
        text = (title + " " + desc).strip()
        if not text:
            continue
        pub = parse_pubdate(it.get("pubDate", ""))
        w = recency_weight(pub, now) * source_weight(it.get("_host", ""))
        texts.append(text)
        weights.append(w)
    return texts, weights

def weighted_aggregate(results: List[Dict[str, float]], weights: List[float]) -> Dict[str, float]:
    if not results:
        return {"POSITIVE": 0.0, "NEGATIVE": 0.0, "NEUTRAL": 0.0}
    w = np.array(weights if weights else [1.0]*len(results), dtype=float)
    w = np.clip(w, 1e-6, None)
    pos = np.average([r["POSITIVE"] for r in results], weights=w)
    neg = np.average([r["NEGATIVE"] for r in results], weights=w)
    neu = np.average([r["NEUTRAL"] for r in results], weights=w)
    return {"POSITIVE": round(pos,4), "NEGATIVE": round(neg,4), "NEUTRAL": round(neu,4)}

def credit_signal(score: dict) -> float:
    # 간단 지표: (pos - neg) * 100
    return round(100.0 * (score.get("POSITIVE",0.0) - score.get("NEGATIVE",0.0)), 2)


# =========================
# 외부 API: 네이버 뉴스(검색)
# =========================
def get_naver_news(query: str, display: int = NEWS_PER_PAGE, start: int = 1, sort: str = "sim") -> List[Dict]:
    # 네이버 뉴스 검색은 키 필요: NAVER_CLIENT_ID/NAVER_CLIENT_SECRET
    headers = {
        "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID",""),
        "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET",""),
    }
    params = {"query": query, "display": display, "start": start, "sort": sort}
    r = requests.get("https://openapi.naver.com/v1/search/news.json",
                     headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json().get("items", [])

def collect_news_for_company(company_name: str) -> List[Dict]:
    import requests
    all_items = []
    start = 1
    for _ in range(MAX_PAGES):
        items = get_naver_news(f"\"{company_name}\"", display=NEWS_PER_PAGE, start=start, sort="sim")
        if not items:
            break
        all_items.extend(items)
        start += NEWS_PER_PAGE
        time.sleep(SLEEP_BETWEEN_CALLS)
    return dedup_by_title_host(all_items)


# =========================
# 번역(OpenAI) + 감성(FinBERT)
# =========================
def init_openai() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 필요합니다(.env 또는 OS 환경변수).")
    return OpenAI(api_key=key)

def translate_ko_en_openai(texts: List[str], client: OpenAI) -> List[str]:
    if not texts:
        return []
    out: List[str] = []
    B = int(OPENAI_TRANSLATE_BATCH or 20)
    system_prompt = (
        "You are a professional financial news translator. "
        "Translate Korean to natural, newsroom-style English. "
        "Preserve entities, figures, and tickers precisely. "
        "Return ONLY the translated sentence without any extra words or quotes."
    )
    for i in range(0, len(texts), B):
        batch = texts[i:i+B]
        for t in batch:
            retries = 3
            backoff = 1.5
            while True:
                try:
                    resp = client.responses.create(
                        model=OPENAI_TRANSLATE_MODEL,
                        temperature=OPENAI_TRANSLATE_TEMPERATURE,
                        input=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"KR: {t}\nEN:"}
                        ],
                    )
                    translated = resp.output_text.strip()
                    out.append(translated)
                    break
                except Exception as e:
                    retries -= 1
                    if retries <= 0:
                        out.append(t)  # 실패 시 원문 유지
                        print(f"[WARN] OpenAI translate failed, fallback original. err={e}")
                        break
                    time.sleep(backoff)
                    backoff *= 2
    return out

def init_finbert_pipeline():
    # 주의: torch 2.6+ 필요(.bin 안전 로드)
    return pipeline("text-classification", model=FINBERT_MODEL, top_k=None)

LABEL_MAP = {"positive": "POSITIVE", "negative": "NEGATIVE", "neutral": "NEUTRAL"}

def finbert_scores(en_texts: List[str], finbert) -> List[Dict[str,float]]:
    outputs = finbert(en_texts)  # 각 문장당 [{'label': 'positive', 'score': ...} x3]
    results = []
    for scores in outputs:
        d = {"POSITIVE": 0.0, "NEGATIVE": 0.0, "NEUTRAL": 0.0}
        for s in scores:
            lab = LABEL_MAP.get(s["label"].lower())
            if lab:
                d[lab] = float(s["score"])
        results.append(d)
    return results


# =========================
# 메인 파이프라인
# =========================
def compute_news_signal_for_companies(df: pd.DataFrame) -> pd.Series:
    """
    df[COMPANY_COL]을 기준으로 회사별 뉴스 스코어를 계산하고
    동일 회사명 행에 동일한 score를 채워 Series로 반환.
    """
    # 중복 호출 방지 캐시
    cache: Dict[str, float] = {}

    # 외부 의존 초기화 1회
    client = init_openai()
    finbert = init_finbert_pipeline()

    signals = []
    for name in df[COMPANY_COL].astype(str).fillna("").tolist():
        if name in cache:
            signals.append(cache[name])
            continue

        items = collect_news_for_company(name)
        texts, weights = build_inputs(items)
        if not texts:
            sig = 0.0
        else:
            en_texts = translate_ko_en_openai(texts, client)
            results = finbert_scores(en_texts, finbert)
            agg = weighted_aggregate(results, weights)
            sig = credit_signal(agg)

        cache[name] = sig
        signals.append(sig)

    return pd.Series(signals, index=df.index, name="news_credit_signal")


def train_and_eval(train_df: pd.DataFrame, target_col: str = TARGET_COL):
    # corp_code 등 식별키는 제거 권장(있으면)
    for col in ["corp_code"]:
        if col in train_df.columns:
            train_df = train_df.drop(columns=[col])

    # 타깃 분리
    if target_col not in train_df.columns:
        raise ValueError(f"타깃 열 '{target_col}' 이(가) 데이터에 없습니다.")
    y = train_df[target_col]
    X = train_df.drop(columns=[target_col])

    # 범주형 → 원핫
    X_enc = pd.get_dummies(X, drop_first=True)

    # 타깃 인코딩
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X_enc, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    model = xgb.XGBClassifier(
        objective="multi:softmax",
        num_class=len(le.classes_),
        eval_metric="mlogloss",
        use_label_encoder=False
    )

    print("\n--- 모델 학습 시작 ---")
    model.fit(X_train, y_train)
    print("--- 모델 학습 완료 ---")

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n모델 예측 정확도: {acc*100:.2f}%")
    print("\n--- 상세 평가 리포트 ---")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    return model, le, X_enc.columns  # 모델, 라벨인코더, 학습시 사용한 컬럼셋


def predict_new(new_df: pd.DataFrame, model, le: LabelEncoder, feature_cols: pd.Index) -> pd.DataFrame:
    # 새 데이터에는 타깃이 없다고 가정 (있으면 drop)
    new_df = new_df.copy()
    if TARGET_COL in new_df.columns:
        new_df = new_df.drop(columns=[TARGET_COL])

    # corp_code 같은 식별자도 제거 권장
    for col in ["corp_code"]:
        if col in new_df.columns:
            new_df = new_df.drop(columns=[col])

    # 범주형 원핫 → 학습 컬럼에 맞춰 정렬/보정
    new_enc = pd.get_dummies(new_df)
    new_reindexed = new_enc.reindex(columns=feature_cols, fill_value=0)

    pred_id = model.predict(new_reindexed)
    pred_label = le.inverse_transform(pred_id)
    out = new_df.copy()
    out["predicted_Grade"] = pred_label
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_path", required=True, help="학습용 stock.xlsx 경로")
    parser.add_argument("--new_path", default=None, help="새 데이터 엑셀/CSV 경로(옵션)")
    parser.add_argument("--save_enriched", default="enriched_stock_with_news.csv", help="뉴스 신호 병합 저장 경로")
    parser.add_argument("--save_preds", default="predictions.csv", help="새 데이터 예측 결과 저장 경로")
    args = parser.parse_args()

    load_dotenv()

    # 1) 학습 데이터 로드
    train_path = args.train_path
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"학습 파일을 찾을 수 없습니다: {train_path}")

    if train_path.lower().endswith(".xlsx"):
        df = pd.read_excel(train_path)
    else:
        df = pd.read_csv(train_path)

    if COMPANY_COL not in df.columns:
        raise ValueError(f"'{COMPANY_COL}' 열이 필요합니다. (회사명 컬럼)")

    # 2) 회사별 뉴스 기반 신용 신호 계산 & 병합
    print("\n[1/3] 회사별 뉴스 신용 신호 계산 중 ...")
    news_signal = compute_news_signal_for_companies(df)
    df_enriched = df.copy()
    df_enriched["news_credit_signal"] = news_signal

    # 저장(기록용)
    df_enriched.to_csv(args.save_enriched, index=False, encoding="utf-8-sig")
    print(f"뉴스 신호 병합 데이터 저장: {args.save_enriched}")

    # 3) 학습/평가
    print("\n[2/3] XGBoost 학습/평가 ...")
    model, le, feature_cols = train_and_eval(df_enriched, target_col=TARGET_COL)

    # 4) 새 데이터 예측 (옵션)
    if args.new_path:
        print("\n[3/3] 새 데이터 예측 ...")
        new_path = args.new_path
        if not os.path.exists(new_path):
            raise FileNotFoundError(f"새 데이터 파일을 찾을 수 없습니다: {new_path}")
        if new_path.lower().endswith(".xlsx"):
            new_df = pd.read_excel(new_path)
        else:
            new_df = pd.read_csv(new_path)
        # 새 데이터에도 뉴스 신호 붙이기
        if COMPANY_COL not in new_df.columns:
            raise ValueError(f"(새 데이터) '{COMPANY_COL}' 열이 필요합니다.")
        new_news_signal = compute_news_signal_for_companies(new_df)
        new_df_enriched = new_df.copy()
        new_df_enriched["news_credit_signal"] = new_news_signal

        preds = predict_new(new_df_enriched, model, le, feature_cols)
        preds.to_csv(args.save_preds, index=False, encoding="utf-8-sig")
        print(f"예측 결과 저장: {args.save_preds}")

if __name__ == "__main__":
    main()
