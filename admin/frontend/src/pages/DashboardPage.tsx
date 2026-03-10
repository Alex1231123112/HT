import { useNavigate } from "react-router-dom";
import { useCustom } from "@refinedev/core";

type StatsOut = {
  total: number;
  horeca: number;
  retail: number;
  active_content: number;
  new_today?: number;
  new_week?: number;
  new_month?: number;
  active_promotions?: number;
  active_news?: number;
  active_deliveries?: number;
};

export function DashboardPage() {
  const navigate = useNavigate();
  const { result: statsResp } = useCustom<StatsOut>({ url: "/dashboard/stats", method: "get" });
  const { result: chartResp } = useCustom<{ daily_growth: Array<{ date: string; count: number }> }>({
    url: "/dashboard/users-chart",
    method: "get",
  });
  const { result: activityResp } = useCustom<{ items: Array<{ id: number; action: string; details?: string; created_at: string }> }>({
    url: "/dashboard/activity",
    method: "get",
  });
  const { result: scheduledResp } = useCustom<{ tasks: Record<string, { last_run: string | null; success_count: number; error_count: number; last_error: string | null; running: boolean }> }>({
    url: "/scheduled-tasks",
    method: "get",
  });
  const stats = statsResp?.data;
  const usersChart = statsResp ? (chartResp?.data?.daily_growth ?? []) : [];
  const logs = activityResp?.data?.items ?? [];
  const scheduledTasks = scheduledResp?.data?.tasks ?? {};

  return (
    <>
      <section className="card grid">
        <div>Пользователи: {stats?.total ?? 0}</div>
        <div>HoReCa: {stats?.horeca ?? 0}</div>
        <div>Retail: {stats?.retail ?? 0}</div>
        <div>Новые за день: {stats?.new_today ?? 0}</div>
        <div>Новые за неделю: {stats?.new_week ?? 0}</div>
        <div>Новые за месяц: {stats?.new_month ?? 0}</div>
        <div>Активный контент: {stats?.active_content ?? 0}</div>
        <div>Активные акции: {stats?.active_promotions ?? 0}</div>
        <div>Активные новинки: {stats?.active_news ?? 0}</div>
        <div>Активные приходы: {stats?.active_deliveries ?? 0}</div>
      </section>

      <section className="card">
        <h3>Рост пользователей</h3>
        {usersChart.map((point: { date: string; count: number }) => (
          <div key={point.date} className="bar-row">
            <span>{point.date}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${Math.max(point.count, 1) * 12}px` }} />
            </div>
            <span>{point.count}</span>
          </div>
        ))}
      </section>

      <section className="card">
        <h3>Быстрые действия</h3>
        <div className="row left wrap">
          <button onClick={() => navigate("/promotions")}>Новая акция</button>
          <button onClick={() => navigate("/analytics")}>Отчет</button>
          <button onClick={() => navigate("/users")}>Экспорт пользователей</button>
        </div>
      </section>

      <section className="card">
        <h3>Периодические задачи</h3>
        <div className="grid-form">
          {Object.entries(scheduledTasks).map(([name, t]) => (
            <div key={name} className="row">
              <span>{name === "content_plan" ? "Content Plan" : "S3 Cleanup"}</span>
              <span>{t.running ? "Работает" : "Остановлен"}</span>
              <span>Последний запуск: {t.last_run ?? "—"}</span>
              <span>OK: {t.success_count}</span>
              <span>Ошибок: {t.error_count}</span>
              {t.last_error && <span className="muted" title={t.last_error}>Ошибка: {t.last_error.slice(0, 80)}{t.last_error.length > 80 ? "…" : ""}</span>}
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h3>Последняя активность</h3>
        {logs.slice(0, 10).map((item: { id: number; action: string; details?: string; created_at: string }) => (
          <div key={item.id} className="row">
            <span>
              {item.action} {item.details ? `- ${item.details}` : ""}
            </span>
            <span>{item.created_at}</span>
          </div>
        ))}
      </section>
    </>
  );
}
