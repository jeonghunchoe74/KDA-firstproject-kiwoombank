import { useState, useEffect, useCallback } from "react";
import {
  Search,
  Building2,
  Bell,
  Plus,
  CheckCircle2,
  Building,
} from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Card } from "./ui/card";
import { allCompanies, CompanyData } from "./companyDatabase";
import kiwoomLogo from "figma:asset/7edd7880e1ed1575f3f3496ccc95c4ca1ab02475.png";
import axios from "axios";

const API_BASE = import.meta?.env?.VITE_API_BASE_URL || "http://localhost:8000";

export interface Company {
  name: string;
  rating: string;
  loanAmount: number;
  interestRate: number;
  delinquency: string;
  collateral: string;
  rm: string;
  ratingChange: string;
}

export interface Notification {
  id: number;
  type: "down" | "up" | "warning";
  companyName: string;
  title: string;
  ratingChange?: string;
  newsKeywords: string;
  timestamp: string;
  isRead: boolean;
}

interface MainDashboardProps {
  onSearchCompany: (companyName: string) => void;
  onViewMyList: () => void;
  onViewNotifications: (notifications: Notification[]) => void;
  unreadCount: number;
  onAddToMyCompanies: (companyName: string) => void;
  myCompanies: Company[];
}

export function MainDashboard({
  onSearchCompany,
  onViewMyList,
  onViewNotifications,
  unreadCount,
  onAddToMyCompanies,
  myCompanies,
}: MainDashboardProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<CompanyData[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [prevRatings, setPrevRatings] = useState<Record<string, string>>({});
  const [polling, setPolling] = useState(false);

  const POLL_INTERVAL = 5 * 60 * 1000; // 5분마다 백엔드 체크

  const getRatingOrder = (rating: string) => {
    const map: Record<string, number> = {
      AAA: 1,
      "AA+": 2,
      AA: 3,
      "AA-": 4,
      "A+": 5,
      A: 6,
      "A-": 7,
      "BBB+": 8,
      BBB: 9,
      "BBB-": 10,
      "BB+": 11,
      BB: 12,
      "BB-": 13,
      "B+": 14,
      B: 15,
      "B-": 16,
      "CCC+": 17,
      CCC: 18,
      "CCC-": 19,
      CC: 20,
      C: 21,
      D: 22,
    };
    return map[rating] || 999;
  };

  // 📡 등급 감시 (백엔드 analyze_many)
  const fetchCompanyRatings = useCallback(async () => {
    if (polling || myCompanies.length === 0) return;
    setPolling(true);
    try {
      const res = await axios.post(`${API_BASE}/analyze_many`, {
        companies: myCompanies.map((c) => c.name),
      });
      const results = res.data?.results || [];

      results.forEach((r: any) => {
        const prev = prevRatings[r.company];
        const next = r.predicted_grade;
        if (!next) return;

        if (prev && prev !== next) {
          const direction = getRatingOrder(next) < getRatingOrder(prev) ? "up" : "down";
          const newNotif: Notification = {
            id: Date.now(),
            type: direction,
            companyName: r.company,
            title: `${r.company} 등급 ${direction === "up" ? "상승" : "하락"}`,
            ratingChange: `${prev} → ${next}`,
            newsKeywords: r.news_keywords || "신용등급 변동",
            timestamp: new Date().toLocaleString("ko-KR"),
            isRead: false,
          };
          setNotifications((prevList) => [newNotif, ...prevList]);
        }
        setPrevRatings((prevMap) => ({ ...prevMap, [r.company]: next }));
      });
    } catch (e) {
      console.error("등급 감시 실패:", e);
    } finally {
      setPolling(false);
    }
  }, [polling, myCompanies, prevRatings]);

  useEffect(() => {
    fetchCompanyRatings();
    const timer = setInterval(fetchCompanyRatings, POLL_INTERVAL);
    return () => clearInterval(timer);
  }, [fetchCompanyRatings]);

  // 🔍 검색
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const filtered = allCompanies.filter((c) =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setSearchResults(filtered);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10">
                <img src={kiwoomLogo} alt="logo" />
              </div>
              <span className="text-slate-700">키움은행</span>
            </div>
            <div className="h-8 w-px bg-slate-300"></div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#AD1765] to-[#8B1252] flex items-center justify-center">
                <span className="text-white tracking-tight">ACI</span>
              </div>
              <span className="text-slate-900">AI Credit Insight</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={() => onViewNotifications(notifications)}
              variant="outline"
              className="border-[#AD1765] text-[#AD1765] hover:bg-[#AD1765]/10 relative"
            >
              <Bell className="w-4 h-4 mr-2" />
              알림함
              {notifications.filter((n) => !n.isRead).length > 0 && (
                <Badge className="absolute -top-2 -right-2 bg-red-600 text-white">
                  {notifications.filter((n) => !n.isRead).length}
                </Badge>
              )}
            </Button>

            <Button
              onClick={onViewMyList}
              variant="outline"
              className="border-[#AD1765] text-[#AD1765] hover:bg-[#AD1765]/10"
            >
              <Building2 className="w-4 h-4 mr-2" />
              관리 기업 목록
            </Button>
          </div>
        </div>
      </header>

      {/* 메인 검색 UI 그대로 유지 */}
      <div className="max-w-4xl mx-auto px-6 pt-32">
        <div className="text-center mb-12">
          <h1 className="text-slate-900 mb-4">기업 신용등급을 분석하세요</h1>
          <p className="text-slate-600">
            AI 기반 실시간 신용등급 분석 및 모니터링 서비스
          </p>
        </div>

        <form onSubmit={handleSearch} className="relative">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-400 w-6 h-6" />
          <Input
            type="text"
            placeholder="분석할 기업명을 입력하세요."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-16 pl-16 pr-6 bg-white border-slate-300 shadow-lg rounded-2xl"
          />
          <Button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-gradient-to-r from-[#AD1765] to-[#8B1252]"
          >
            검색
          </Button>
        </form>

        {/* 검색결과 UI 그대로 유지 */}
        {searchResults.length > 0 && (
          <div className="mt-8 grid gap-4">
            {searchResults.map((c) => (
              <Card key={c.name} className="p-6 shadow-lg hover:shadow-xl">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-slate-900">{c.name}</h3>
                      <Badge className="bg-[#AD1765]/10 text-[#AD1765] border-[#AD1765]/20">
                        {c.rating}
                      </Badge>
                      <Badge variant="outline" className="text-slate-600">
                        {c.industry}
                      </Badge>
                    </div>
                    <p className="text-slate-600 mb-4">{c.description}</p>
                    <div className="flex gap-3">
                      <Button
                        onClick={() => onSearchCompany(c.name)}
                        className="bg-gradient-to-r from-[#AD1765] to-[#8B1252]"
                      >
                        ACI신용등급 확인
                      </Button>
                      <Button
                        onClick={() => onAddToMyCompanies(c.name)}
                        variant="outline"
                        className="border-[#AD1765] text-[#AD1765]"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        관심기업 목록에 추가
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
