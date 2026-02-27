import type { AccessControlProvider, AuthProvider, DataProvider, HttpError } from "@refinedev/core";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
const CSRF_TOKEN = import.meta.env.VITE_CSRF_TOKEN ?? "dev-csrf";
const TOKEN_KEY = "token";

type WrappedResponse<T = unknown> = { message?: string; data?: T };

const readToken = () => localStorage.getItem(TOKEN_KEY) ?? "";

const request = async <T = unknown>(path: string, init?: RequestInit, csrf = false): Promise<T> => {
  const token = readToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(csrf ? { "X-CSRF-Token": CSRF_TOKEN } : {}),
    ...(init?.headers ?? {}),
  };

  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
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
    const list = payload as unknown[];
    return { data: list as any[], total: list.length };
  },
  getOne: async ({ resource, id }) => {
    if (resource === "settings") {
      const payload = await request<unknown>(toResourcePath(resource));
      const data = unwrapData<Record<string, string>>(payload);
      return { data: { id: String(id), key: String(id), value: data[String(id)] ?? "" } };
    }
    const payload = await request<unknown>(`${toResourcePath(resource)}/${id}`);
    return { data: payload as any };
  },
  create: async ({ resource, variables }) => {
    if (resource === "settings") {
      const items = Object.entries(variables as Record<string, string>).map(([key, value]) => ({ key, value }));
      await request("/settings", { method: "PUT", body: JSON.stringify({ items }) }, true);
      return { data: { ...variables } as any };
    }
    const payload = await request<unknown>(
      toResourcePath(resource),
      {
        method: "POST",
        body: JSON.stringify(variables ?? {}),
      },
      true,
    );
    return { data: payload as any };
  },
  update: async ({ resource, id, variables }) => {
    if (resource === "settings") {
      const item = variables as { key: string; value: string };
      await request("/settings", { method: "PUT", body: JSON.stringify({ items: [{ key: item.key, value: item.value }] }) }, true);
      return { data: { id: item.key, ...item } as any };
    }
    const payload = await request<unknown>(
      `${toResourcePath(resource)}/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(variables ?? {}),
      },
      true,
    );
    return { data: payload as any };
  },
  deleteOne: async ({ resource, id }) => {
    const payload = await request<unknown>(`${toResourcePath(resource)}/${id}`, { method: "DELETE" }, true);
    return { data: ((payload as Record<string, unknown>) ?? { id }) as any };
  },
  getApiUrl: () => API_URL,
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
    return { data: unwrapData<Record<string, unknown>>(response) as any };
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
    const token = readToken();
    if (!token) return { authenticated: false, redirectTo: "/login" };
    try {
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
    if (resource === "users" || resource === "logs") {
      return { can: role === "superadmin" || role === "admin" };
    }
    if (resource === "mailings" && (action === "delete" || action === "create" || action === "edit")) {
      return { can: role !== "manager" };
    }
    return { can: true };
  },
};

