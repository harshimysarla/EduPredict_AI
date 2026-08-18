const BASE = "/api"

export class ApiError extends Error {
  status: number
  detail: string
  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

export function getToken(): string | null {
  return localStorage.getItem("edupredict_token") ?? sessionStorage.getItem("edupredict_token")
}

export function setToken(token: string | null) {
  // When a session is restored from sessionStorage keep it there; otherwise
  // the caller decides whether to persist across browser restarts.
  if (token) {
    if (!localStorage.getItem("edupredict_token") && !sessionStorage.getItem("edupredict_token")) {
      localStorage.setItem("edupredict_token", token)
    }
  } else {
    localStorage.removeItem("edupredict_token")
    sessionStorage.removeItem("edupredict_token")
  }
}

/** Remember-me: persist the token in localStorage (survives browser restart) or
 * sessionStorage (cleared when the browser closes). Returns the storage used. */
export function setTokenWithRemember(token: string, remember: boolean): "local" | "session" {
  localStorage.removeItem("edupredict_token")
  sessionStorage.removeItem("edupredict_token")
  if (remember) {
    localStorage.setItem("edupredict_token", token)
    return "local"
  }
  sessionStorage.setItem("edupredict_token", token)
  return "session"
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers })

  if (res.status === 401 && !path.startsWith("/auth/")) {
    setToken(null)
    window.dispatchEvent(new Event("edupredict:unauthorized"))
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (typeof body.detail === "string") detail = body.detail
      else if (Array.isArray(body.detail)) {
        detail = body.detail
          .map((d: { msg?: string }) => d.msg ?? "")
          .join("; ")
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "PUT",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "PATCH",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  upload: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", body: formData }),
}
