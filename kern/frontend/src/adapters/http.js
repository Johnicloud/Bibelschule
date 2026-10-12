// Gemeinsamer HTTP-Aufruf aller Adapter.
export function createCall(base) {
  return async function call(method, path, body) {
    const res = await fetch(base + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
    }
    return res.status === 204 ? null : res.json()
  }
}
