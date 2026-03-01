function getApiUrl(): string {
  if (typeof window !== "undefined" && (window as { __API_URL__?: string }).__API_URL__) {
    return (window as { __API_URL__: string }).__API_URL__;
  }
  return import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
}
const CSRF_TOKEN = import.meta.env.VITE_CSRF_TOKEN ?? "dev-csrf";

let token = localStorage.getItem("token") ?? "";

export const setToken = (value: string) => {
  token = value;
  localStorage.setItem("token", value);
};

export const clearToken = () => {
  token = "";
  localStorage.removeItem("token");
};

const headers = (csrf = false): HeadersInit => ({
  "Content-Type": "application/json",
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
  ...(csrf ? { "X-CSRF-Token": CSRF_TOKEN } : {}),
});

const headersNoContentType = (csrf = false): HeadersInit => ({
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
  ...(csrf ? { "X-CSRF-Token": CSRF_TOKEN } : {}),
});

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiUrl()}${path}`, { headers: headers() });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiPost<T>(path: string, body: unknown, csrf = false): Promise<T> {
  const response = await fetch(`${getApiUrl()}${path}`, {
    method: "POST",
    headers: headers(csrf),
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${getApiUrl()}${path}`, {
    method: "PUT",
    headers: headers(true),
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiUrl()}${path}`, { method: "DELETE", headers: headers(true) });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiDownload(path: string): Promise<string> {
  const response = await fetch(`${getApiUrl()}${path}`, { headers: headers() });
  if (!response.ok) throw new Error(await response.text());
  return response.text();
}

export async function apiUploadMedia(
  file: File,
): Promise<{ filename: string; size: number; url?: string }> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${getApiUrl()}/upload`, {
    method: "POST",
    headers: headersNoContentType(true),
    body,
  });
  if (!response.ok) throw new Error(await response.text());
  const payload = (await response.json()) as {
    message: string;
    data: { filename: string; size: number; url?: string };
  };
  return payload.data;
}
