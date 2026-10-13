// Anwendungsschicht: Anmeldung. Kennt nur den "api"-Port, nicht HTTP.
export function createAuthService(api) {
  return {
    me: () => api.me(),
    login: (username, password) => api.login(username.trim(), password),
    logout: () => api.logout(),
  }
}
