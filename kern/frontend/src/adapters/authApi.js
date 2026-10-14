// Ausgehender Adapter: Anmeldung beim Kern (Sitzung läuft über ein httpOnly-Cookie, kein Token im JS).
import { createCall } from './http'

export function createAuthApi(base = '/api') {
  const call = createCall(base)
  return {
    me: () => call('GET', '/me'),
    login: (username, password) => call('POST', '/login', { username, password }),
    logout: () => call('POST', '/logout'),
    changePassword: (oldPassword, newPassword) =>
      call('PUT', '/me/password', { old_password: oldPassword, new_password: newPassword }),
    updateProfile: (vorname, nachname, gemeinde) => call('PUT', '/me', { vorname, nachname, gemeinde }),
    accounts: () => call('GET', '/accounts'),
    createAccount: (username, password, isAdmin) => call('POST', '/accounts', { username, password, is_admin: isAdmin }),
  }
}
