import { Outlet } from "react-router-dom";

import { useAdmin } from "../context/AdminContext";
import { AppHeader } from "./AppHeader";

export function AdminShell() {
  const { loading, error, notice } = useAdmin();
  return (
    <main className="container">
      <AppHeader />
      {error && <p className="error">{error}</p>}
      {notice && <p className="notice">{notice}</p>}
      {loading && <p className="muted">Обновление данных...</p>}
      <Outlet />
    </main>
  );
}
