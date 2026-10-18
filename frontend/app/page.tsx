import Link from "next/link";

export default function HomePage() {
  return (
    <main className="container mx-auto py-16 px-4 text-center">
      <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
        AI SCM 재고 최적화 플랫폼
      </h1>
      <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
        LangGraph 멀티 에이전트 기반 수요 예측 및 적정 발주량 자동 제안 시스템
      </p>
      <div className="mt-8">
        <Link
          href="/orders"
          className="inline-flex items-center px-6 py-3 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors shadow-sm"
        >
          발주 제안 검토 대시보드 바로가기
        </Link>
      </div>
    </main>
  );
}
