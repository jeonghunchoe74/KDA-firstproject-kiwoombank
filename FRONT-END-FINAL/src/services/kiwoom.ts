import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

export async function fetchMetrics(codes: string[]) {
    const res = await api.get("/metrics", {
        params: {
            codes,
            all_periods: true,
    },
});
  return res.data.data; // 서버 응답이 { data: [...] } 형태임
}

export async function fetchNewsSentiment(codes: string[]) {
const res = await api.get("/news/sentiment", {
    params: {
    codes,
    days: 7,
    limit: 10,
    },
});
  return res.data.results; // 결과 리스트
}

export async function fetchCreditRatings(codes: string[]) {
const res = await api.get("/credit/ratings", {
    params: {
    codes,
    },
});
  return res.data; // ratings, skipped 등 포함
}