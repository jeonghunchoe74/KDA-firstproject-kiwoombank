// 전체 기업 데이터베이스
export interface CompanyData {
  name: string;
  
  industry: string;
  description: string;
}

export const allCompanies: CompanyData[] = [
  {
    name: "삼성전자",
    industry: "반도체·전자",
    description:
      "메모리·시스템반도체(파운드리 포함)와 모바일·TV·가전·네트워크 장비를 설계·제조하는 종합 전자기업.",
  },
  {
    name: "삼성디스플레이",
    industry: "디스플레이",
    description:
      "스마트폰·IT·TV 등용 OLED·QD‑OLED 패널을 개발·양산하는 디스플레이 전문회사.",
  },
  {
    name: "삼성SDI",
    industry: "이차전지·소재",
    description:
      "전기차 배터리·ESS·소형전지와 반도체·디스플레이용 전자재료를 생산하는 에너지·소재 기업.",
  },
  {
    name: "삼성전기",
    industry: "전자부품",
    description:
      "MLCC, 카메라/통신 모듈, 기판 등 핵심 전자부품을 개발·제조하는 종합 부품사.",
  },
  {
    name: "삼성SDS",
    industry: "IT서비스·디지털물류",
    description:
      "클라우드·AI 기반의 IT 서비스와 디지털 물류 플랫폼을 제공하는 디지털 전환( DX ) 기업.",
  },
  {
    name: "삼성바이오로직스",
    industry: "바이오 CDMO",
    description:
      "바이오의약품의 위탁개발·제조(CDMO)부터 완제충전·품질분석까지 통합 서비스를 제공.",
  },
  {
    name: "삼성바이오에피스",
    industry: "바이오시밀러",
    description:
      "자가면역·종양·안과 등 적응증의 바이오시밀러를 연구·개발·허가·판매하는 바이오기업.",
  },
  {
    name: "삼성생명",
    industry: "생명보험",
    description:
      "생명보험·연금·보장성 상품과 자산운용을 통해 장기 보험서비스를 제공.",
  },
  {
    name: "삼성화재",
    industry: "손해보험",
    description:
      "자동차·일반·장기손해보험과 기업 리스크 솔루션을 제공하는 종합 손보사.",
  },
  {
    name: "삼성카드",
    industry: "신용카드·결제",
    description:
      "신용·체크·법인카드 등 결제와 생활금융 서비스를 제공하는 전업 카드사.",
  },
  {
    name: "삼성증권",
    industry: "종합금융투자",
    description:
      "자산관리(WM)·글로벌마켓·IB·운용 등을 아우르는 종합 금융투자회사.",
  },
  {
    name: "삼성선물",
    industry: "파생·선물중개",
    description:
      "국내·해외 파생상품 및 FX 브로커리지, 리서치·리스크관리 컨설팅을 제공하는 선물사.",
  },
  {
    name: "삼성자산운용",
    industry: "자산운용",
    description:
      "공모·사모펀드 및 ETF(KODEX) 등 다양한 운용 상품을 제공하는 국내 대표 자산운용사.",
  },
  {
    name: "삼성벤처투자",
    industry: "CVC·벤처캐피탈",
    description:
      "그룹 CVC 역할로 신기술·스타트업에 투자하고 오픈이노베이션을 추진.",
  },
  {
    name: "삼성중공업",
    industry: "조선·해양플랜트",
    description:
      "LNG 운반선·해양 시추·생산설비 등 선박·해양플랜트의 설계·건조를 수행.",
  },
  {
    name: "삼성이앤에이",
    industry: "EPC·플랜트엔지니어링",
    description:
      "정유·석유화학·가스, 에너지 전환·환경·산업설비 등 글로벌 플랜트의 설계·조달·시공(EPC) 및 O&M을 수행.",
  },
  {
    name: "삼성물산",
    industry: "건설·상사·패션·리조트",
    description:
      "건축/토목/플랜트, 글로벌 트레이딩, 패션 브랜드, 리조트/레저 사업을 영위하는 지주형 종합상사.",
  },
  {
    name: "삼성글로벌리서치",
    industry: "싱크탱크·경영연구",
    description:
      "삼성그룹 싱크탱크로서 국내외 경제·산업·경영 연구와 관계사 경영진단을 수행.",
  },
  {
    name: "삼성의료원",
    industry: "의료·연구",
    description:
      "삼성서울병원·강북삼성병원·삼성창원병원 등을 중심으로 진료·연구·교육을 수행하는 의료기관 체계.",
  },
  {
    name: "삼성웰스토리",
    industry: "푸드서비스·식자재유통",
    description:
      "오피스/산업체/병원/대학·골프장 급식과 식자재 유통, F&B 솔루션을 제공하는 식음 서비스 기업.",
  },
  {
    name: "키움증권",
    industry: "종합증권·온라인브로커리지",
    description:
      "온라인 중심의 브로커리지·리테일과 IB·자산운용 기능을 갖춘 종합 증권사.",
  },
  {
    name: "키움투자자산운용",
    industry: "자산운용",
    description:
      "집합투자·일임/자문 및 ETF 운용 등 다양한 투자상품을 제공하는 자산운용사.",
  },
  {
    name: "키움저축은행",
    industry: "저축은행·소매금융",
    description:
      "여·수신, 개인신용·모기지 등 소매금융 중심의 저축은행 서비스 제공.",
  },
  {
    name: "키움예스저축은행",
    industry: "저축은행·디지털뱅킹",
    description:
      "디지털·모바일 중심의 대출·수신 상품을 제공하는 저축은행.",
  },
  {
    name: "키움인베스트먼트",
    industry: "PE/VC 투자",
    description:
      "벤처·그로스·바이아웃 등 다양한 전략으로 국내외 기업에 투자하는 투자운용사.",
  },
  {
    name: "키움에셋플래너",
    industry: "보험GA·재무설계",
    description:
      "다수 보험사와 제휴해 보장/은퇴/자산관리 설계를 제공하는 종합 보험대리점(GA).",
  },
  {
    name: "키움프라이빗에쿼티",
    industry: "사모투자(PE)",
    description:
      "기업가치 제고를 위한 사모투자펀드 운용 및 구조화 투자를 수행.",
  },
  {
    name: "키움캐피탈",
    industry: "여신전문금융",
    description:
      "신기술금융·시설리스·기업/부동산 금융과 스탁론 등 여신전문금융 서비스를 제공.",
  },
  {
    name: "키움에프앤아이",
    industry: "NPL·자산유동화",
    description:
      "부실채권(NPL) 투자·자산유동화 및 담보자산 관리 등 특수자산 투자 전문회사.",
  },
];