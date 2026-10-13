// Gemeinsamer HTTP-Aufruf aller Adapter.
import { loggedIn } from '../state/auth'

export function createCall(base) {
  return async function call(method, path, body) {
    const res = await fetch(base + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    if (res.status === 401) loggedIn.value = false   // Sitzung fehlt/abgelaufen: überall zurück zum Login
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
    }
    return res.status === 204 ? null : res.json()
  }
}
