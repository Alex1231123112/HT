import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPost, apiPut, clearToken, setToken } from "./api";
import "./styles.css";

type User = {
  id: number;
  username: string | null;
  user_type: "horeca" | "retail" | "all";
  establishment: string;
};

type ContentItem = {
  id: number;
  title: string;
  description: string;
  user_type: "horeca" | "retail" | "all";
  is_active: boolean;
};

type DashboardStats = {
  total: number;
  horeca: number;
  retail: number;
  active_content: number;
  total_mailings: number;
};

type GenericResp = { message: string; data?: Record<string, unknown> };
type LogsResponse = { message: string; data: { items: Array<{ id: number; action: string; created_at: string }> } };
type SettingsResponse = { message: string; data: Record<string, string> };

type Tab =
  | "dashboard"
  | "users"
  | "promotions"
  | "news"
  | "deliveries"
  | "mailings"
  | "analytics"
  | "settings"
  | "logs";

export default function App() {
  const [tokenReady, setTokenReady] = useState<boolean>(Boolean(localStorage.getItem("token")));
  const [tab, setTab] = useState<Tab>("dashboard");
  const [themeDark, setThemeDark] = useState(false);
  const [search, setSearch] = useState("");
  const [users, setUsers] = useState<User[]>([]);
  const [promotions, setPromotions] = useState<ContentItem[]>([]);
  const [news, setNews] = useState<ContentItem[]>([]);
  const [deliveries, setDeliveries] = useState<ContentItem[]>([]);
  const [mailings, setMailings] = useState<Array<{ id: number; text: string; status: string }>>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [logs, setLogs] = useState<Array<{ id: number; action: string; created_at: string }>>([]);
  const [systemSettings, setSystemSettings] = useState<Record<string, string>>({});
  const [login, setLogin] = useState({ username: "admin", password: "change-me" });
  const [mailText, setMailText] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    const [u, p, n, d, m, s, lg, st] = await Promise.all([
      apiGet<User[]>("/users"),
      apiGet<ContentItem[]>("/promotions"),
      apiGet<ContentItem[]>("/news"),
      apiGet<ContentItem[]>("/deliveries"),
      apiGet<Array<{ id: number; text: string; status: string }>>("/mailings"),
      apiGet<DashboardStats>("/dashboard/stats"),
      apiGet<LogsResponse>("/logs?limit=20"),
      apiGet<SettingsResponse>("/settings"),
    ]);
    setUsers(u);
    setPromotions(p);
    setNews(n);
    setDeliveries(d);
    setMailings(m);
    setStats(s);
    setLogs(lg.data.items);
    setSystemSettings(st.data ?? {});
  };

  const logout = async () => {
    try {
      await apiPost("/auth/logout", {}, false);
    } finally {
      clearToken();
      setTokenReady(false);
    }
  };

  useEffect(() => {
    if (tokenReady) {
      void refresh().catch((e) => setError(String(e)));
    }
  }, [tokenReady]);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const data = await apiPost<{ access_token: string }>("/auth/login", login);
      setToken(data.access_token);
      setTokenReady(true);
    } catch (err) {
      setError(String(err));
    }
  };

  const createDemoPromotion = async () => {
    await apiPost(
      "/promotions",
      {
        title: "Новая акция",
        description: "Скидка для сегмента HoReCa",
        user_type: "horeca",
        is_active: true,
      },
      true,
    );
    await refresh();
  };

  const createNews = async () => {
    await apiPost(
      "/news",
      {
        title: "Новая новинка",
        description: "Тестовая новинка",
        user_type: "all",
        is_active: true,
      },
      true,
    );
    await refresh();
  };

  const createDelivery = async () => {
    await apiPost(
      "/deliveries",
      {
        title: "Новый приход",
        description: "Тестовый приход",
        user_type: "all",
        is_active: true,
      },
      true,
    );
    await refresh();
  };

  const createMailing = async () => {
    await apiPost(
      "/mailings",
      {
        text: mailText,
        target_type: "all",
        media_type: "none",
      },
      true,
    );
    setMailText("");
    await refresh();
  };

  const sendMailing = async (id: number) => {
    await apiPost(`/mailings/${id}/send`, {}, true);
    await refresh();
  };

  const toggleUser = async (user: User) => {
    await apiPut(`/users/${user.id}`, { is_active: false });
    await refresh();
  };

  const deletePromotion = async (id: number) => {
    await apiDelete(`/promotions/${id}`);
    await refresh();
  };

  const saveSettings = async () => {
    const items = Object.entries(systemSettings).map(([key, value]) => ({ key, value }));
    await apiPut<GenericResp>("/settings", { items });
    await refresh();
  };

  const filteredUsers = useMemo(
    () =>
      users.filter(
        (user) =>
          (user.username ?? "").toLowerCase().includes(search.toLowerCase()) ||
          user.establishment.toLowerCase().includes(search.toLowerCase()),
      ),
    [users, search],
  );

  if (!tokenReady) {
    return (
      <main className="container">
        <h1>Admin Login</h1>
        <form onSubmit={handleLogin} className="card">
          <input value={login.username} onChange={(e) => setLogin({ ...login, username: e.target.value })} />
          <input type="password" value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })} />
          <button type="submit">Login</button>
        </form>
        {error && <p className="error">{error}</p>}
      </main>
    );
  }

  return (
    <main className={`container ${themeDark ? "theme-dark" : ""}`}>
      <header className="row">
        <h1>Админ-панель</h1>
        <div className="row">
          <button onClick={() => setThemeDark((v) => !v)}>{themeDark ? "Светлая тема" : "Темная тема"}</button>
          <button onClick={logout}>Выйти</button>
        </div>
      </header>
      {error && <p className="error">{error}</p>}
      <nav className="tabs">
        {(["dashboard", "users", "promotions", "news", "deliveries", "mailings", "analytics", "settings", "logs"] as Tab[]).map(
          (item) => (
            <button key={item} className={tab === item ? "active-tab" : ""} onClick={() => setTab(item)}>
              {item}
            </button>
          ),
        )}
      </nav>

      {tab === "dashboard" && (
        <section className="card grid">
          <div>Пользователи: {stats?.total ?? 0}</div>
          <div>HoReCa: {stats?.horeca ?? 0}</div>
          <div>Retail: {stats?.retail ?? 0}</div>
          <div>Активный контент: {stats?.active_content ?? 0}</div>
          <div>Рассылки: {stats?.total_mailings ?? 0}</div>
        </section>
      )}

      {tab === "users" && (
        <section className="card">
          <h2>Users</h2>
          <input placeholder="Search user or establishment" value={search} onChange={(e) => setSearch(e.target.value)} />
          {filteredUsers.map((user) => (
            <div key={user.id} className="row">
              <span>
                {user.id} | {user.username ?? "no_username"} | {user.establishment}
              </span>
              <button onClick={() => toggleUser(user)}>Deactivate</button>
            </div>
          ))}
        </section>
      )}

      {tab === "promotions" && (
        <section className="card">
          <h2>Promotions</h2>
          <button onClick={createDemoPromotion}>Create Demo Promotion</button>
          {promotions.map((item) => (
            <div key={item.id} className="row">
              <span>{item.title}</span>
              <button onClick={() => deletePromotion(item.id)}>Delete</button>
            </div>
          ))}
        </section>
      )}

      {tab === "news" && (
        <section className="card">
          <h2>News</h2>
          <button onClick={createNews}>Create News</button>
          {news.map((item) => (
            <div key={item.id} className="row">
              <span>{item.title}</span>
            </div>
          ))}
        </section>
      )}

      {tab === "deliveries" && (
        <section className="card">
          <h2>Deliveries</h2>
          <button onClick={createDelivery}>Create Delivery</button>
          {deliveries.map((item) => (
            <div key={item.id} className="row">
              <span>{item.title}</span>
            </div>
          ))}
        </section>
      )}

      {tab === "mailings" && (
        <section className="card">
          <h2>Mailings</h2>
          <div className="row">
            <input value={mailText} onChange={(e) => setMailText(e.target.value)} placeholder="Mailing text" />
            <button onClick={createMailing}>Create</button>
          </div>
          {mailings.map((mailing) => (
            <div key={mailing.id} className="row">
              <span>
                #{mailing.id} {mailing.text} ({mailing.status})
              </span>
              <button onClick={() => sendMailing(mailing.id)}>Send</button>
            </div>
          ))}
        </section>
      )}

      {tab === "analytics" && (
        <section className="card">
          <h2>Analytics</h2>
          <p>Используйте API `GET /api/analytics/*` и экспорт `GET /api/analytics/export`.</p>
        </section>
      )}

      {tab === "settings" && (
        <section className="card">
          <h2>Settings</h2>
          {Object.entries(systemSettings).map(([key, value]) => (
            <div className="row" key={key}>
              <span>{key}</span>
              <input
                value={value}
                onChange={(e) =>
                  setSystemSettings((prev) => ({
                    ...prev,
                    [key]: e.target.value,
                  }))
                }
              />
            </div>
          ))}
          <button onClick={saveSettings}>Save settings</button>
        </section>
      )}

      {tab === "logs" && (
        <section className="card">
          <h2>Logs</h2>
          {logs.map((item) => (
            <div className="row" key={item.id}>
              <span>
                #{item.id} {item.action}
              </span>
              <span>{item.created_at}</span>
            </div>
          ))}
        </section>
      )}
    </main>
  );
}
