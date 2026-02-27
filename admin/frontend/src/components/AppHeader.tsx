import { NavLink } from "react-router-dom";

import { useAdmin } from "../context/AdminContext";

const NAV_ITEMS: Array<{ to: string; label: string; roles?: Array<"superadmin" | "admin" | "manager"> }> = [
  { to: "/dashboard", label: "Дашборд" },
  { to: "/users", label: "Пользователи", roles: ["superadmin", "admin"] },
  { to: "/promotions", label: "Акции" },
  { to: "/news", label: "Новинки" },
  { to: "/deliveries", label: "Приходы" },
  { to: "/mailings", label: "Рассылки" },
  { to: "/analytics", label: "Аналитика" },
  { to: "/settings", label: "Настройки", roles: ["superadmin"] },
  { to: "/logs", label: "Логи", roles: ["superadmin", "admin"] },
];

export function AppHeader() {
  const { logout, role } = useAdmin();
  return (
    <header className="row">
      <h1>Админ-панель</h1>
      <div className="row left wrap">
        {NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(role)).map((item) => (
          <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "active-tab" : "")}>
            {item.label}
          </NavLink>
        ))}
        {role === "superadmin" && (
          <NavLink to="/admins" className={({ isActive }) => (isActive ? "active-tab" : "")}>
            Админы
          </NavLink>
        )}
      </div>
      <div className="row">
        <span className="muted">Роль: {role}</span>
        <button onClick={logout}>Выйти</button>
      </div>
    </header>
  );
}
