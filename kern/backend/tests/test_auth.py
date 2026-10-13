from app.domain.auth import hash_password, verify_password


def test_hash_is_salted_and_not_the_plain_password():
    h = hash_password("geheim123")
    assert "geheim123" not in h and "$" in h


def test_same_password_hashes_differently_each_time():
    assert hash_password("geheim123") != hash_password("geheim123")


def test_verify_accepts_correct_and_rejects_wrong_password():
    h = hash_password("geheim123")
    assert verify_password("geheim123", h) is True
    assert verify_password("falsch", h) is False


def test_verify_rejects_malformed_hash():
    assert verify_password("geheim123", "kein-hash-format") is False
