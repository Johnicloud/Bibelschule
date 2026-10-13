class NotFound(Exception):
    pass


class InvalidInput(Exception):
    pass


class Unauthorized(Exception):
    """Falsches Login oder keine/abgelaufene Sitzung."""
