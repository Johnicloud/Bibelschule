// Anwendungsschicht: Anmeldung. Kennt nur den "api"-Port, nicht HTTP.
export function createAuthService(api) {
  return {
    me: () => api.me(),
    login: (username, password) => api.login(username.trim(), password),
    logout: () => api.logout(),
    changePassword: (oldPassword, newPassword) => api.changePassword(oldPassword, newPassword),
    updateProfile: (vorname, nachname, gemeinde) =>
      api.updateProfile((vorname || '').trim(), (nachname || '').trim(), (gemeinde || '').trim()),
    accounts: () => api.accounts(),
    createAccount: (username, password, isAdmin) => api.createAccount(username.trim(), password, isAdmin),
    setAdmin: (username, isAdmin) => api.setAdmin(username, isAdmin),
    resetPassword: (username) => api.resetPassword(username),
  }
}
