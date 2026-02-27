import { useState } from "react";
import { useCustom } from "@refinedev/core";

export function AnalyticsPage() {
  const { result: usersResp } = useCustom<Record<string, number>>({ url: "/analytics/users", method: "get" });
  const { result: mailingsResp } = useCustom<Record<string, number>>({ url: "/analytics/mailings", method: "get" });
  const { result: contentResp } = useCustom<Record<string, number>>({ url: "/analytics/content", method: "get" });
  const { result: cohortResp } = useCustom<{ rows: Array<{ cohort: string; users: number }> }>({ url: "/analytics/cohort", method: "get" });
  const { result: conversionResp } = useCustom<Record<string, number>>({ url: "/analytics/conversions", method: "get" });
  const usersAnalytics = usersResp?.data ?? {};
  const mailingsAnalytics = mailingsResp?.data ?? {};
  const contentAnalytics = contentResp?.data ?? {};
  const cohortRows = cohortResp?.data?.rows ?? [];
  const conversionAnalytics = conversionResp?.data ?? {};
  const exportAnalytics = async () => {
    const response = await fetch(`${import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"}/analytics/export`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token") ?? ""}` },
    });
    const content = await response.text();
    const blob = new Blob([content], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "analytics.csv";
    link.click();
    URL.revokeObjectURL(url);
  };
  const [tab, setTab] = useState<"users" | "mailings" | "content" | "conversions">("users");

  return (
    <section className="card">
      <div className="row left">
        <button onClick={() => setTab("users")}>Пользователи</button>
        <button onClick={() => setTab("mailings")}>Рассылки</button>
        <button onClick={() => setTab("content")}>Контент</button>
        <button onClick={() => setTab("conversions")}>Конверсии</button>
        <button onClick={exportAnalytics}>Экспорт CSV</button>
      </div>

      {tab === "users" && (
        <div className="grid">
          <div className="card nested">
            <h3>Ключевые метрики</h3>
            <p>Всего: {usersAnalytics.total ?? 0}</p>
            <p>Активные: {usersAnalytics.active ?? 0}</p>
            <p>Новые за месяц: {usersAnalytics.new_month ?? 0}</p>
          </div>
          <div className="card nested">
            <h3>Сегменты</h3>
            <p>HoReCa: {usersAnalytics.horeca ?? 0}</p>
            <p>Retail: {usersAnalytics.retail ?? 0}</p>
          </div>
          <div className="card nested">
            <h3>Когортная таблица</h3>
            {cohortRows.map((row: { cohort: string; users: number }) => (
              <div key={row.cohort} className="row">
                <span>{row.cohort}</span>
                <span>{row.users}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "mailings" && (
        <div className="grid">
          <div className="card nested">
            <p>Всего: {mailingsAnalytics.total ?? 0}</p>
            <p>Sent: {mailingsAnalytics.sent ?? 0}</p>
            <p>Delivered: {mailingsAnalytics.delivered ?? 0}</p>
          </div>
          <div className="card nested">
            <p>Open rate: {mailingsAnalytics.open_rate ?? 0}%</p>
            <p>CTR: {mailingsAnalytics.ctr ?? 0}%</p>
            <p>Clicked: {mailingsAnalytics.clicked ?? 0}</p>
          </div>
        </div>
      )}

      {tab === "content" && (
        <div className="grid">
          <div className="card nested">
            <p>Promotions: {contentAnalytics.promotions ?? 0}</p>
            <p>News: {contentAnalytics.news ?? 0}</p>
            <p>Deliveries: {contentAnalytics.deliveries ?? 0}</p>
          </div>
        </div>
      )}

      {tab === "conversions" && (
        <div className="card nested">
          <p>Delivered: {conversionAnalytics.delivered ?? 0}</p>
          <p>Clicked: {conversionAnalytics.clicked ?? 0}</p>
          <p>Conversion rate: {conversionAnalytics.conversion_rate ?? 0}%</p>
        </div>
      )}
    </section>
  );
}
