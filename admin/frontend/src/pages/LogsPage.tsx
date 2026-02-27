import { useState } from "react";

import { useAdmin } from "../context/AdminContext";

export function LogsPage() {
  const { filteredLogs, logFilter, setLogFilter, exportLogs } = useAdmin();
  const [actionFilter, setActionFilter] = useState("all");
  const [adminFilter, setAdminFilter] = useState("all");
  const [periodFilter, setPeriodFilter] = useState<"all" | "today" | "week" | "month">("all");

  const list = filteredLogs
    .filter((item) => (actionFilter === "all" ? true : item.action === actionFilter))
    .filter((item) => (adminFilter === "all" ? true : String(item.admin_id ?? "none") === adminFilter))
    .filter((item) => {
      if (periodFilter === "all") return true;
      const now = Date.now();
      const created = new Date(item.created_at).getTime();
      const diff = now - created;
      if (periodFilter === "today") return diff <= 24 * 60 * 60 * 1000;
      if (periodFilter === "week") return diff <= 7 * 24 * 60 * 60 * 1000;
      return diff <= 30 * 24 * 60 * 60 * 1000;
    });
  const actions = Array.from(new Set(filteredLogs.map((item) => item.action))).sort((a, b) => a.localeCompare(b));
  const admins = Array.from(new Set(filteredLogs.map((item) => String(item.admin_id ?? "none"))));

  return (
    <section className="card">
      <h2>Логи действий</h2>
      <div className="row left">
        <input placeholder="Поиск в логах" value={logFilter} onChange={(e) => setLogFilter(e.target.value)} />
        <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
          <option value="all">Все действия</option>
          {actions.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select value={adminFilter} onChange={(e) => setAdminFilter(e.target.value)}>
          <option value="all">Все админы</option>
          {admins.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select value={periodFilter} onChange={(e) => setPeriodFilter(e.target.value as "all" | "today" | "week" | "month")}>
          <option value="all">Период: всё время</option>
          <option value="today">Сегодня</option>
          <option value="week">Неделя</option>
          <option value="month">Месяц</option>
        </select>
        <button onClick={exportLogs}>Экспорт CSV</button>
      </div>
      {list.map((item) => (
        <div className="row" key={item.id}>
          <span>
            #{item.id} {item.action} {item.details ? `- ${item.details}` : ""}
          </span>
          <span>{item.created_at}</span>
        </div>
      ))}
    </section>
  );
}
