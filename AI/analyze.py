import argparse
import numpy as np
from naver_news import collect_news
from preprocess import dedup_by_title_host, build_inputs
from sentiment_finbert import analyze_texts_ko, weighted_aggregate
from utils_scoring import credit_signal
from config import MAX_PAGES, NEWS_PER_PAGE


def run(company: str):
    """
    기업명(company)을 입력받아:
    1) 네이버 뉴스 수집
    2) OpenAI 번역 + FinBERT 감성 분석
    3) 뉴스 기반 신용 피처(news_sentiment_score 등) 계산
    """

    query = f'"{company}"'
    items = collect_news(query, max_pages=MAX_PAGES, per_page=NEWS_PER_PAGE)
    items = dedup_by_title_host(items)

    texts, weights = build_inputs(items)
    if not texts:
        print("No news fetched.")
        return

    # 1️⃣ 감성 분석
    results = analyze_texts_ko(texts)

    # 2️⃣ 가중 평균 스코어 계산
    agg = weighted_aggregate(results, weights)
    news_sentiment_score = credit_signal(agg)

    # 3️⃣ 추가 피처 계산
    news_count = len(texts)
    diffs = [r["POSITIVE"] - r["NEGATIVE"] for r in results]
    sentiment_volatility = float(np.std(diffs))                     # 감성 변동성
    positive_ratio = sum(1 for r in results if r["POSITIVE"] > max(r["NEGATIVE"], r["NEUTRAL"])) / news_count
    negative_ratio = sum(1 for r in results if r["NEGATIVE"] > max(r["POSITIVE"], r["NEUTRAL"])) / news_count
    recency_weight_mean = float(np.mean(weights)) if weights else 0.0

    # 4️⃣ 결과 출력
    print(f"\n[ {company} ] 총 {news_count}건 분석")
    print("가중 평균 스코어:", agg)
    print(f"뉴스 기반 신용 신호 (news_sentiment_score): {news_sentiment_score}")
    print(f"뉴스 수 (news_count): {news_count}")
    print(f"뉴스 감성 변동성 (sentiment_volatility): {sentiment_volatility:.4f}")
    print(f"긍정 비율 (positive_ratio): {positive_ratio:.4f}")
    print(f"부정 비율 (negative_ratio): {negative_ratio:.4f}")
    print(f"최근성 평균 가중치 (recency_weight_mean): {recency_weight_mean:.4f}")

    # 5️⃣ 결과 반환 (데이터프레임에 쉽게 붙이기 용이)
    return {
        "company": company,
        "news_sentiment_score": round(news_sentiment_score, 2),
        "news_count": news_count,
        "sentiment_volatility": round(sentiment_volatility, 4),
        "positive_ratio": round(positive_ratio, 4),
        "negative_ratio": round(negative_ratio, 4),
        "recency_weight_mean": round(recency_weight_mean, 4),
        "agg": agg,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="뉴스 감성 기반 신용 피처 분석")
    parser.add_argument("company", type=str, help="회사명 (예: 삼성전자, 쿠팡)")
    args = parser.parse_args()
    run(args.company)
