from app.core.token_vault import TokenVault


def test_token_round_trip() -> None:
    vault = TokenVault()
    original = "fake-development-access-token"

    encrypted = vault.encrypt(original)

    assert encrypted != original
    assert vault.decrypt(encrypted) == original
