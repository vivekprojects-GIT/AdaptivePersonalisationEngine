const TOKEN_KEY = 'access_token'
const GUEST_KEY = 'guest_id'

export function getAccessToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setAccessToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearAccessToken() {
  localStorage.removeItem(TOKEN_KEY)
}

/** Decode a JWT payload without verifying the signature (client-side only —
 *  the server is always the real authority). Returns null on any malformed token. */
function decodePayload(token: string): { exp?: number; sub?: string } | null {
  try {
    const part = token.split('.')[1]
    if (!part) return null
    const json = atob(part.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json)
  } catch {
    return null
  }
}

/** True when a token exists and has not expired. Used by the router guard and
 *  nav to decide signed-in state. An expired token is treated as signed-out. */
export function isAuthenticated(): boolean {
  const token = getAccessToken()
  if (!token) return false
  const payload = decodePayload(token)
  if (!payload) return false
  if (typeof payload.exp === 'number' && payload.exp * 1000 <= Date.now()) {
    clearAccessToken()
    return false
  }
  return true
}

/** Stable per-browser guest identity (no login required). Sent as the
 *  X-Guest-Id header so APE's per-user learning works for anonymous users. */
export function getGuestId(): string {
  try {
    let g = localStorage.getItem(GUEST_KEY)
    if (!g) {
      g = Math.random().toString(36).slice(2, 10) + Date.now().toString(36)
      localStorage.setItem(GUEST_KEY, g)
    }
    return g
  } catch {
    return 'anon0000'
  }
}
