const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
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

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { headers: headers() });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiPost<T>(path: string, body: unknown, csrf = false): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: headers(csrf),
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "PUT",
    headers: headers(true),
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { method: "DELETE", headers: headers(true) });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
