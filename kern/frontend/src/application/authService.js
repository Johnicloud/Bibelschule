// Anwendungsschicht: Anmeldung. Kennt nur den "api"-Port, nicht HTTP.
export function createAuthService(api) {
  return {
    me: () => api.me(),
    login: (username, password) => api.login(username.trim(), password),
    logout: () => api.logout(),
    changePassword: (oldPassword, newPassword) => api.changePassword(oldPassword, newPassword),
    accounts: () => api.accounts(),
    createAccount: (username, password) => api.createAccount(username.trim(), password),
  }
}
