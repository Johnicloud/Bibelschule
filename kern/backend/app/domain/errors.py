class NotFound(Exception):
    pass


class InvalidInput(Exception):
    pass


class Unauthorized(Exception):
    """Falsches Login oder keine/abgelaufene Sitzung."""


class Forbidden(Exception):
    """Angemeldet, aber ohne die nötige Berechtigung (z. B. kein Admin)."""
