import { useMemo, useState } from "react";

import { apiDelete, apiDownload, apiGet, apiPost, apiPut, apiUploadMedia, clearToken, setToken } from "../api";
import {
  AdminAccount,
  BackupsResponse,
  ContentItem,
  ContentKind,
  DashboardStats,
  GenericDataResponse,
  GenericResp,
  LogsResponse,
  Mailing,
  MailingStats,
  SettingsResponse,
  User,
} from "../types";

export function useAdminData() {
  const [tokenReady, setTokenReady] = useState<boolean>(Boolean(localStorage.getItem("token")));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [role, setRole] = useState<"superadmin" | "admin" | "manager">("manager");
  const [search, setSearch] = useState("");
  const [userTypeFilter, setUserTypeFilter] = useState<"all" | "horeca" | "retail">("all");
  const [users, setUsers] = useState<User[]>([]);
  const [promotions, setPromotions] = useState<ContentItem[]>([]);
  const [news, setNews] = useState<ContentItem[]>([]);
  const [deliveries, setDeliveries] = useState<ContentItem[]>([]);
  const [mailings, setMailings] = useState<Mailing[]>([]);
  const [mailingPreview, setMailingPreview] = useState("");
  const [mailingStats, setMailingStats] = useState<Record<number, MailingStats>>({});
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [logs, setLogs] = useState<Array<{ id: number; action: string; details?: string; admin_id?: number; created_at: string }>>([]);
  const [logFilter, setLogFilter] = useState("");
  const [systemSettings, setSystemSettings] = useState<Record<string, string>>({});
  const [backups, setBackups] = useState<string[]>([]);
  const [usersChart, setUsersChart] = useState<Array<{ date: string; count: number }>>([]);
  const [usersAnalytics, setUsersAnalytics] = useState<Record<string, number>>({});
  const [mailingsAnalytics, setMailingsAnalytics] = useState<Record<string, number>>({});
  const [contentAnalytics, setContentAnalytics] = useState<Record<string, number>>({});
  const [cohortRows, setCohortRows] = useState<Array<{ cohort: string; users: number }>>([]);
  const [conversionAnalytics, setConversionAnalytics] = useState<Record<string, number>>({});
  const [admins, setAdmins] = useState<AdminAccount[]>([]);
  const [login, setLoginState] = useState({ username: "admin", password: "change-me", remember: false });
  const [mailForm, setMailForm] = useState({
    text: "",
    target_type: "all" as "all" | "horeca" | "retail" | "custom",
    media_type: "none" as "none" | "photo" | "video",
    media_url: "",
    scheduled_at: "",
    establishment: "",
    speed: "medium" as "high" | "medium" | "low",
  });
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [creatingUser, setCreatingUser] = useState({
    id: "",
    username: "",
    first_name: "",
    last_name: "",
    user_type: "horeca" as "horeca" | "retail",
    establishment: "",
  });
  const [contentForms, setContentForms] = useState<Record<ContentKind, ContentItem>>({
    promotions: { id: 0, title: "", description: "", image_url: "", user_type: "all", is_active: true, published_at: "" },
    news: { id: 0, title: "", description: "", image_url: "", user_type: "all", is_active: true, published_at: "" },
    deliveries: { id: 0, title: "", description: "", image_url: "", user_type: "all", is_active: true, published_at: "" },
  });

  const fetchMe = async () => {
    const me = await apiGet<GenericResp>("/auth/me");
    const currentRole = (me.data?.role ?? "manager") as "superadmin" | "admin" | "manager";
    setRole(currentRole);
  };

  const refresh = async () => {
    setLoading(true);
    try {
      await fetchMe();
      const [u, p, n, d, m, s, lg, st, backupResp, au, am, ac, chart, cohort, conversions] = await Promise.all([
        apiGet<User[]>("/users"),
        apiGet<ContentItem[]>("/promotions"),
        apiGet<ContentItem[]>("/news"),
        apiGet<ContentItem[]>("/deliveries"),
        apiGet<Mailing[]>("/mailings"),
        apiGet<DashboardStats>("/dashboard/stats"),
        apiGet<LogsResponse>("/logs?limit=50"),
        apiGet<SettingsResponse>("/settings"),
        apiGet<BackupsResponse>("/settings/backups"),
        apiGet<GenericDataResponse>("/analytics/users"),
        apiGet<GenericDataResponse>("/analytics/mailings"),
        apiGet<GenericDataResponse>("/analytics/content"),
        apiGet<GenericDataResponse>("/dashboard/users-chart"),
        apiGet<GenericDataResponse>("/analytics/cohort"),
        apiGet<GenericDataResponse>("/analytics/conversions"),
      ]);
      setUsers(u);
      setPromotions(p);
      setNews(n);
      setDeliveries(d);
      setMailings(m);
      setStats(s);
      setLogs(lg.data.items);
      setSystemSettings(st.data ?? {});
      setBackups(backupResp.data.files ?? []);
      setUsersAnalytics(au.data as unknown as Record<string, number>);
      setMailingsAnalytics(am.data as unknown as Record<string, number>);
      setContentAnalytics(ac.data as unknown as Record<string, number>);
      setUsersChart(((chart.data?.daily_growth as Array<{ date: string; count: number }> | undefined) ?? []).slice(-14));
      setCohortRows((cohort.data?.rows as Array<{ cohort: string; users: number }>) ?? []);
      setConversionAnalytics(conversions.data as unknown as Record<string, number>);
      try {
        const adminsResp = await apiGet<{ message: string; data: { items: AdminAccount[] } }>("/admins");
        setAdmins(adminsResp.data.items);
      } catch {
        setAdmins([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const loginWithCredentials = async () => {
    setError("");
    const payload = await apiPost<{ access_token: string }>("/auth/login", {
      username: login.username,
      password: login.password,
      remember_me: login.remember,
    });
    setToken(payload.access_token);
    setTokenReady(true);
    setNotice("Успешный вход.");
    await refresh();
  };

  const logout = async () => {
    try {
      await apiPost("/auth/logout", {}, false);
    } finally {
      clearToken();
      setTokenReady(false);
      setNotice("");
      setError("");
    }
  };

  const exportTextFile = async (path: string, filename: string, mime = "text/csv") => {
    const content = await apiDownload(path);
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const createUser = async () => {
    const id = Number(creatingUser.id);
    if (!id || !creatingUser.establishment.trim()) {
      setError("Для создания пользователя нужны id и заведение.");
      return;
    }
    await apiPost(
      "/users",
      {
        id,
        username: creatingUser.username || null,
        first_name: creatingUser.first_name || null,
        last_name: creatingUser.last_name || null,
        user_type: creatingUser.user_type,
        establishment: creatingUser.establishment,
        is_active: true,
      },
      true,
    );
    setCreatingUser({ id: "", username: "", first_name: "", last_name: "", user_type: "horeca", establishment: "" });
    setNotice("Пользователь создан.");
    await refresh();
  };

  const saveUser = async () => {
    if (!editingUser) return;
    await apiPut(`/users/${editingUser.id}`, {
      username: editingUser.username,
      first_name: editingUser.first_name,
      last_name: editingUser.last_name,
      user_type: editingUser.user_type,
      establishment: editingUser.establishment,
      is_active: editingUser.is_active ?? true,
    });
    setEditingUser(null);
    setNotice("Пользователь обновлен.");
    await refresh();
  };

  const deleteUser = async (id: number) => {
    await apiDelete(`/users/${id}`);
    setNotice("Пользователь удален.");
    await refresh();
  };

  const saveContent = async (kind: ContentKind) => {
    const form = contentForms[kind];
    if (!form.title.trim()) {
      setError("Заголовок обязателен.");
      return;
    }
    const payload = {
      title: form.title,
      description: form.description,
      image_url: form.image_url || null,
      user_type: form.user_type,
      published_at: form.published_at || null,
      is_active: form.is_active,
    };
    if (form.id) {
      await apiPut(`/${kind}/${form.id}`, payload);
    } else {
      await apiPost(`/${kind}`, payload, true);
    }
    setContentForms((prev) => ({
      ...prev,
      [kind]: { id: 0, title: "", description: "", image_url: "", user_type: "all", is_active: true, published_at: "" },
    }));
    await refresh();
  };

  const deleteContent = async (kind: ContentKind, id: number) => {
    await apiDelete(`/${kind}/${id}`);
    await refresh();
  };

  const duplicatePromotion = async (id: number) => {
    await apiPost(`/promotions/${id}/duplicate`, {}, true);
    await refresh();
  };

  const uploadContentMedia = async (kind: ContentKind, file: File | null) => {
    if (!file) return;
    const data = await apiUploadMedia(file);
    const mediaUrl = data.url ?? (data.filename ? `/uploads/${data.filename}` : "");
    setContentForms((prev) => ({ ...prev, [kind]: { ...prev[kind], image_url: mediaUrl } }));
  };

  const uploadMailMedia = async (file: File | null) => {
    if (!file) return;
    const data = await apiUploadMedia(file);
    const mediaUrl = data.url ?? (data.filename ? `/uploads/${data.filename}` : "");
    setMailForm((prev) => ({ ...prev, media_url: mediaUrl }));
  };

  const createMailing = async () => {
    if (!mailForm.text.trim()) {
      setError("Текст рассылки обязателен.");
      return;
    }
    let customTargets: number[] | null = null;
    if (mailForm.target_type === "custom") {
      customTargets = users.filter((item) => item.establishment === mailForm.establishment).map((item) => item.id);
    }
    await apiPost(
      "/mailings",
      {
        text: mailForm.text,
        target_type: mailForm.target_type,
        media_type: mailForm.media_type,
        media_url: mailForm.media_url || null,
        custom_targets: customTargets,
        scheduled_at: mailForm.scheduled_at || null,
        speed: mailForm.speed,
      },
      true,
    );
    setMailForm({
      text: "",
      target_type: "all",
      media_type: "none",
      media_url: "",
      scheduled_at: "",
      establishment: "",
      speed: "medium",
    });
    await refresh();
  };

  const sendTestMailing = async (mailingId: number) => {
    await apiPost(`/mailings/${mailingId}/test-send`, {}, true);
    setNotice("Тестовая отправка выполнена.");
  };

  const previewMailing = async (id: number) => {
    const response = await apiPost<GenericResp>(`/mailings/${id}/preview`, {}, false);
    setMailingPreview(`Текст: ${String(response.data?.text ?? "")}\nМедиа: ${String(response.data?.media ?? "нет")}`);
  };

  const sendMailing = async (id: number) => {
    await apiPost(`/mailings/${id}/send`, {}, true);
    await refresh();
  };

  const cancelMailing = async (id: number) => {
    await apiPost(`/mailings/${id}/cancel`, {}, true);
    await refresh();
  };

  const retryMailing = async (id: number) => {
    await apiPost(`/mailings/${id}/retry`, {}, true);
    await refresh();
  };

  const deleteMailing = async (id: number) => {
    await apiDelete(`/mailings/${id}`);
    await refresh();
  };

  const fetchMailingStats = async (id: number) => {
    const response = await apiGet<GenericResp>(`/mailings/${id}/stats`);
    setMailingStats((prev) => ({ ...prev, [id]: response.data as unknown as MailingStats }));
  };

  const createBackup = async () => {
    await apiPost("/settings/backup", {}, true);
    await refresh();
  };

  const saveSettings = async () => {
    const items = Object.entries(systemSettings).map(([key, value]) => ({ key, value }));
    await apiPut("/settings", { items });
    setNotice("Настройки сохранены.");
    await refresh();
  };

  const createAdmin = async (payload: { username: string; password: string; role: "superadmin" | "admin" | "manager" }) => {
    await apiPost("/admins", payload, true);
    await refresh();
  };

  const updateAdmin = async (id: number, payload: { role?: "superadmin" | "admin" | "manager"; is_active?: boolean }) => {
    await apiPut(`/admins/${id}`, payload);
    await refresh();
  };

  const deleteAdmin = async (id: number) => {
    await apiDelete(`/admins/${id}`);
    await refresh();
  };

  const contentByKind: Record<ContentKind, ContentItem[]> = { promotions, news, deliveries };
  const establishments = useMemo(
    () => Array.from(new Set(users.map((item) => item.establishment))).sort((a, b) => a.localeCompare(b)),
    [users],
  );
  const filteredUsers = useMemo(
    () =>
      users
        .filter((item) => (userTypeFilter === "all" ? true : item.user_type === userTypeFilter))
        .filter(
          (item) =>
            (item.username ?? "").toLowerCase().includes(search.toLowerCase()) ||
            item.establishment.toLowerCase().includes(search.toLowerCase()),
        ),
    [users, search, userTypeFilter],
  );
  const filteredLogs = useMemo(
    () =>
      logs.filter(
        (item) =>
          item.action.toLowerCase().includes(logFilter.toLowerCase()) ||
          (item.details ?? "").toLowerCase().includes(logFilter.toLowerCase()),
      ),
    [logs, logFilter],
  );

  return {
    tokenReady,
    setTokenReady,
    loading,
    error,
    setError,
    notice,
    setNotice,
    role,
    search,
    setSearch,
    userTypeFilter,
    setUserTypeFilter,
    users,
    promotions,
    news,
    deliveries,
    mailings,
    mailingPreview,
    mailingStats,
    stats,
    logs,
    logFilter,
    setLogFilter,
    systemSettings,
    setSystemSettings,
    backups,
    usersChart,
    usersAnalytics,
    mailingsAnalytics,
    contentAnalytics,
    cohortRows,
    conversionAnalytics,
    admins,
    login,
    setLoginState,
    mailForm,
    setMailForm,
    editingUser,
    setEditingUser,
    creatingUser,
    setCreatingUser,
    contentForms,
    setContentForms,
    refresh,
    loginWithCredentials,
    logout,
    exportUsers: () => exportTextFile("/users/export", "users.csv"),
    exportLogs: () => exportTextFile("/logs/export?limit=2000", "logs.csv"),
    exportAnalytics: () => exportTextFile("/analytics/export", "analytics.csv"),
    downloadBackup: (filename: string) => exportTextFile(`/settings/backups/${filename}`, filename, "application/json"),
    createUser,
    saveUser,
    deleteUser,
    saveContent,
    deleteContent,
    duplicatePromotion,
    uploadContentMedia,
    uploadMailMedia,
    createMailing,
    sendTestMailing,
    previewMailing,
    sendMailing,
    cancelMailing,
    retryMailing,
    deleteMailing,
    fetchMailingStats,
    createBackup,
    saveSettings,
    createAdmin,
    updateAdmin,
    deleteAdmin,
    filteredUsers,
    filteredLogs,
    contentByKind,
    establishments,
  };
}
