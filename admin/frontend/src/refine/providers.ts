import type { AccessControlProvider, AuthProvider, DataProvider, HttpError } from "@refinedev/core";

const DEFAULT_API_URL = "http://localhost:8000/api";
const CSRF_TOKEN = import.meta.env.VITE_CSRF_TOKEN ?? "dev-csrf";
const TOKEN_KEY = "token";

declare global {
  interface Window {
    __API_URL__?: string;
  }
}

export function getApiUrl(): string {
  if (typeof window !== "undefined" && window.__API_URL__) return window.__API_URL__;
  return import.meta.env.VITE_API_URL ?? DEFAULT_API_URL;
}

type WrappedResponse<T = unknown> = { message?: string; data?: T };

const readToken = () => localStorage.getItem(TOKEN_KEY) ?? "";

/** Загрузка файла на сервер (локально или S3). Не передаёт Content-Type, чтобы браузер подставил boundary. */
export async function uploadContentFile(file: File): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const token = readToken();
  const headers: HeadersInit = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    "X-CSRF-Token": CSRF_TOKEN,
  };
  const res = await fetch(`${getApiUrl()}/upload`, { method: "POST", headers, body: formData });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail ?? `Ошибка загрузки: ${res.status}`);
  }
  const data = (await res.json()) as { data?: { url?: string; filename?: string } };
  const url = data.data?.url ?? (data.data?.filename ? `/uploads/${data.data.filename}` : "");
  if (!url) throw new Error("Нет URL в ответе");
  return { url };
}

const request = async <T = unknown>(path: string, init?: RequestInit, csrf = false): Promise<T> => {
  const token = readToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(csrf ? { "X-CSRF-Token": CSRF_TOKEN } : {}),
    ...(init?.headers ?? {}),
  };

  const response = await fetch(`${getApiUrl()}${path}`, { ...init, headers });
  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  if (!response.ok) {
    const detail = isJson ? JSON.stringify(await response.json()) : await response.text();
    throw {
      message: detail || `HTTP ${response.status}`,
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
  if (resource === "content_plan") return "/content-plan";
  return `/${resource}`;
};

export const dataProvider: DataProvider = {
  getList: async ({ resource }) => {
    const payload = await request<unknown>(toResourcePath(resource));
    if (resource === "logs" || resource === "admins") {
      const data = unwrapData<{ items: unknown[] }>(payload);
      return { data: data.items ?? [], total: data.items?.length ?? 0 };
    }
    if (resource === "settings") {
      const data = unwrapData<Record<string, string>>(payload);
      const list = Object.entries(data).map(([key, value]) => ({ id: key, key, value }));
      return { data: list, total: list.length };
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
    const payload = await request<unknown>(
      toResourcePath(resource),
      {
        method: "POST",
        body: JSON.stringify(variables ?? {}),
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
    const payload = await request<unknown>(
      `${toResourcePath(resource)}/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(variables ?? {}),
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
    if (resource === "users" || resource === "logs" || resource === "managers" || resource === "establishments") {
      return { can: role === "superadmin" || role === "admin" };
    }
    if (resource === "mailings" && (action === "delete" || action === "create" || action === "edit")) {
      return { can: role !== "manager" };
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

