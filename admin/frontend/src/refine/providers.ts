import type { AccessControlProvider, AuthProvider, DataProvider, HttpError } from "@refinedev/core";

const DEFAULT_API_URL = "http://localhost:8000/api";
const TOKEN_KEY = "token";

let _csrfToken: string | null = null;

async function getCsrfToken(): Promise<string> {
  if (_csrfToken) return _csrfToken;
  const apiBase = getApiUrl();
  const url = apiBase.startsWith("http") ? apiBase.replace(/\/api\/?$/, "") + "/api/csrf-token" : "/api/csrf-token";
  const r = await fetch(url);
  if (!r.ok) throw new Error("Failed to get CSRF token");
  const data = (await r.json()) as { token?: string };
  _csrfToken = data.token ?? "";
  return _csrfToken;
}

declare global {
  interface Window {
    __API_URL__?: string;
  }
}

export function getApiUrl(): string {
  if (typeof window !== "undefined" && window.__API_URL__) return window.__API_URL__;
  // В режиме dev (npm run dev) используем относительный /api — Vite проксирует на backend
  if (import.meta.env.DEV) return "/api";
  return import.meta.env.VITE_API_URL ?? DEFAULT_API_URL;
}

type WrappedResponse<T = unknown> = { message?: string; data?: T };

const readToken = () => localStorage.getItem(TOKEN_KEY) ?? "";

/** Загрузка файла на сервер (локально или S3). Не передаёт Content-Type, чтобы браузер подставил boundary. */
export async function uploadContentFile(file: File): Promise<{ url: string }> {
  const doUpload = async (csrf: string) => {
    const formData = new FormData();
    formData.append("file", file);
    const token = readToken();
    const headers: HeadersInit = {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      "X-CSRF-Token": csrf,
    };
    const res = await fetch(`${getApiUrl()}/upload`, { method: "POST", headers, body: formData });
    if (!res.ok) {
      const err = (await res.json().catch(() => ({}))) as { detail?: string };
      return { ok: false as const, status: res.status, detail: err.detail ?? `Ошибка: ${res.status}` };
    }
    const data = (await res.json()) as { data?: { url?: string; filename?: string } };
    const url = data.data?.url ?? (data.data?.filename ? `/uploads/${data.data.filename}` : "");
    if (!url) return { ok: false as const, status: 0, detail: "Нет URL в ответе" };
    return { ok: true as const, url };
  };
  let csrf = await getCsrfToken();
  let result = await doUpload(csrf);
  if (!result.ok && result.status === 403) {
    _csrfToken = null;
    csrf = await getCsrfToken();
    result = await doUpload(csrf);
  }
  if (!result.ok) throw new Error(result.detail);
  return { url: result.url };
}

const request = async <T = unknown>(path: string, init?: RequestInit, _csrf = false): Promise<T> => {
  const token = readToken();
  const method = (init?.method ?? "GET").toUpperCase();
  const isMutating = method !== "GET" && method !== "HEAD";
  const csrf = isMutating ? await getCsrfToken() : "";
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(isMutating && csrf ? { "X-CSRF-Token": csrf } : {}),
    ...(init?.headers ?? {}),
  };

  const url = `${getApiUrl()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw {
      message: `Не удалось подключиться к API: ${msg}. URL: ${url}. Проверьте, что сервер запущен и доступен.`,
      statusCode: undefined,
    } as HttpError;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  if (!response.ok) {
    let message: string;
    if (isJson) {
      const body = (await response.json()) as { detail?: string | Array<{ msg?: string; loc?: unknown }> };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail) && body.detail.length > 0) {
        message = body.detail.map((d) => d.msg ?? JSON.stringify(d)).join("; ");
      } else {
        message = JSON.stringify(body);
      }
    } else {
      message = await response.text() || `HTTP ${response.status}`;
    }
    throw {
      message: message || `Ошибка ${response.status}`,
      statusCode: response.status,
    } as HttpError;
  }

  if (!isJson) {
    return (await response.text()) as T;
  }

  return (await response.json()) as T;
};

const unwrapData = <T>(payload: unknown): T => {
  if (payload && typeof payload === "object" && "message" in (payload as Record<string, unknown>)) {
    const wrapped = payload as WrappedResponse<T>;
    return (wrapped.data as T) ?? ({} as T);
  }
  return payload as T;
};

const toResourcePath = (resource: string) => {
  if (resource === "settings") return "/settings";
  if (resource === "logs") return "/logs";
  if (resource === "delivery_logs") return "/logs/deliveries";
  if (resource === "content_plan") return "/content-plan";
  return `/${resource}`;
};

export const dataProvider: DataProvider = {
  getList: async ({ resource }) => {
    const payload = await request<unknown>(toResourcePath(resource));
    if (resource === "logs" || resource === "admins" || resource === "delivery_logs") {
      const data = unwrapData<{ items: unknown[] }>(payload);
      return { data: data.items ?? [], total: data.items?.length ?? 0 };
    }
    if (resource === "settings") {
      const data = unwrapData<Record<string, string>>(payload);
      const list = Object.entries(data).map(([key, value]) => ({ id: key, key, value }));
      return { data: list, total: list.length };
    }
    if (resource === "establishments" || resource === "channels") {
      const list = Array.isArray(payload) ? payload : (payload && typeof payload === "object" && "data" in (payload as object) ? (payload as { data: unknown[] }).data : []) ?? [];
      return { data: list as Record<string, unknown>[], total: Array.isArray(list) ? list.length : 0 };
    }
    // API может вернуть массив напрямую или обёртку { data, total }
    if (Array.isArray(payload)) {
      return { data: payload as Record<string, unknown>[], total: payload.length };
    }
    if (payload && typeof payload === "object" && "data" in (payload as object)) {
      const wrapped = payload as { data: unknown[]; total?: number };
      return { data: wrapped.data ?? [], total: wrapped.total ?? wrapped.data?.length ?? 0 };
    }
    return { data: [], total: 0 };
  },
  getOne: async ({ resource, id }) => {
    if (resource === "settings") {
      const payload = await request<unknown>(toResourcePath(resource));
      const data = unwrapData<Record<string, string>>(payload);
      return { data: { id: String(id), key: String(id), value: data[String(id)] ?? "" } };
    }
    const payload = await request<unknown>(`${toResourcePath(resource)}/${id}`);
    return { data: payload as Record<string, unknown> };
  },
  create: async ({ resource, variables }) => {
    if (resource === "settings") {
      const items = Object.entries(variables as Record<string, string>).map(([key, value]) => ({ key, value }));
      await request("/settings", { method: "PUT", body: JSON.stringify({ items }) }, true);
      return { data: { ...(variables as Record<string, unknown>) } };
    }
    let body: unknown = variables ?? {};
    if (resource === "content_plan" && body && typeof body === "object") {
      const v = body as Record<string, unknown>;
      const channelIds = Array.isArray(v.channel_ids)
        ? (v.channel_ids as unknown[]).map((id) => (typeof id === "string" ? parseInt(id, 10) : Number(id)))
        : [];
      const normItem = (it: Record<string, unknown>) => ({
        content_type: it.content_type,
        content_id: it.content_id != null && it.content_id !== "" ? Number(it.content_id) : null,
        custom_title: it.custom_title ?? null,
        custom_description: it.custom_description ?? null,
        custom_media_url: it.custom_media_url ?? null,
      });
      const items = Array.isArray(v.items) ? (v.items as Record<string, unknown>[]).map(normItem) : [];
      body = {
        title: v.title,
        content_type: v.content_type,
        content_id: v.content_id != null && v.content_id !== "" ? Number(v.content_id) : null,
        custom_title: v.custom_title ?? null,
        custom_description: v.custom_description ?? null,
        custom_media_url: v.custom_media_url ?? null,
        scheduled_at: v.scheduled_at ?? null,
        channel_ids: channelIds,
        items,
      };
    }
    const payload = await request<unknown>(
      toResourcePath(resource),
      {
        method: "POST",
        body: JSON.stringify(body),
      },
      true,
    );
    return { data: payload as Record<string, unknown> };
  },
  update: async ({ resource, id, variables }) => {
    if (resource === "settings") {
      const item = variables as { key: string; value: string };
      await request("/settings", { method: "PUT", body: JSON.stringify({ items: [{ key: item.key, value: item.value }] }) }, true);
      return { data: { id: item.key, ...item } };
    }
    let body: unknown = variables ?? {};
    if (resource === "content_plan" && body && typeof body === "object") {
      const v = body as Record<string, unknown>;
      const normItem = (it: Record<string, unknown>) => ({
        content_type: it.content_type,
        content_id: it.content_id != null && it.content_id !== "" ? Number(it.content_id) : null,
        custom_title: it.custom_title ?? null,
        custom_description: it.custom_description ?? null,
        custom_media_url: it.custom_media_url ?? null,
      });
      const items = Array.isArray(v.items) ? (v.items as Record<string, unknown>[]).map(normItem) : undefined;
      body = { ...v, items };
    }
    const payload = await request<unknown>(
      `${toResourcePath(resource)}/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(body),
      },
      true,
    );
    return { data: payload as Record<string, unknown> };
  },
  deleteOne: async ({ resource, id }) => {
    const payload = await request<unknown>(`${toResourcePath(resource)}/${id}`, { method: "DELETE" }, true);
    return { data: ((payload as Record<string, unknown>) ?? { id: String(id) }) };
  },
  getApiUrl: () => getApiUrl(),
  custom: async ({ url, method, payload, query }) => {
    const search = query ? `?${new URLSearchParams(query as Record<string, string>).toString()}` : "";
    const response = await request<unknown>(
      `${url}${search}`,
      {
        method,
        body: payload ? JSON.stringify(payload) : undefined,
      },
      method !== "get",
    );
    return { data: unwrapData<Record<string, unknown>>(response) };
  },
} as DataProvider;

export const authProvider: AuthProvider = {
  login: async (params) => {
    const values = (params ?? {}) as { username?: string; email?: string; identifier?: string; password?: string; remember_me?: boolean };
    const identifier = values.identifier ?? values.username ?? values.email ?? "";
    const password = values.password ?? "";
    const payload = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        identifier,
        email: values.email ?? null,
        username: values.username ?? null,
        password,
        remember_me: Boolean(values.remember_me),
      }),
    });
    localStorage.setItem(TOKEN_KEY, payload.access_token);
    return { success: true, redirectTo: "/dashboard" };
  },
  logout: async () => {
    try {
      await request("/auth/logout", { method: "POST", body: JSON.stringify({}) });
    } catch {
      // Ignore logout network errors and always clear local auth state.
    }
    localStorage.removeItem(TOKEN_KEY);
    return { success: true, redirectTo: "/login" };
  },
  check: async () => {
    try {
      const token = readToken();
      if (!token) return { authenticated: false, redirectTo: "/login" };
      await request("/auth/me");
      return { authenticated: true };
    } catch {
      return { authenticated: false, redirectTo: "/login" };
    }
  },
  getIdentity: async () => {
    const token = readToken();
    if (!token) {
      return { id: "guest", name: "Guest", role: "manager" };
    }
    try {
      const payload = await request<WrappedResponse<{ username: string; role: "superadmin" | "admin" | "manager" }>>("/auth/me");
      const data = payload.data ?? { username: "unknown", role: "manager" };
      return { id: data.username, name: data.username, role: data.role };
    } catch {
      return { id: "guest", name: "Guest", role: "manager" };
    }
  },
  onError: async () => ({ error: undefined }),
};

export const accessControlProvider: AccessControlProvider = {
  can: async ({ resource, action }) => {
    let role: "superadmin" | "admin" | "manager" = "manager";
    try {
      const me = (await authProvider.getIdentity?.()) as { role?: "superadmin" | "admin" | "manager" } | undefined;
      role = me?.role ?? "manager";
    } catch {
      return { can: false };
    }

    if (resource === "settings" || resource === "admins") {
      return { can: role === "superadmin" };
    }
    if (resource === "users" || resource === "logs" || resource === "delivery_logs" || resource === "managers" || resource === "establishments") {
      return { can: role === "superadmin" || role === "admin" };
    }
    if (resource === "channels" && action === "delete") {
      return { can: role === "superadmin" || role === "admin" };
    }
    if (resource === "content_plan" && (action === "delete" || action === "edit")) {
      return { can: role === "superadmin" || role === "admin" };
    }
    if (resource === "events" && action === "delete") {
      return { can: role === "superadmin" || role === "admin" };
    }
    return { can: true };
  },
};

