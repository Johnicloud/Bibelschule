// Ausgehender Adapter: Anmeldung beim Kern (Sitzung läuft über ein httpOnly-Cookie, kein Token im JS).
import { createCall } from './http'

export function createAuthApi(base = '/api') {
  const call = createCall(base)
  return {
    me: () => call('GET', '/me'),
    login: (username, password) => call('POST', '/login', { username, password }),
    logout: () => call('POST', '/logout'),
  }
}
