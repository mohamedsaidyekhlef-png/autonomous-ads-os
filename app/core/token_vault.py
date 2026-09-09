from cryptography.fernet import Fernet, InvalidToken

from app.core.settings import get_settings


class TokenVaultError(RuntimeError):
    pass


class TokenVault:
    def __init__(self) -> None:
        settings = get_settings()

        try:
            self._fernet = Fernet(settings.token_encryption_key.encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise TokenVaultError("TOKEN_ENCRYPTION_KEY is invalid.") from exc

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            raise TokenVaultError("Cannot encrypt an empty token.")

        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            raise TokenVaultError("Cannot decrypt an empty token.")

        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise TokenVaultError("Credential could not be decrypted.") from exc
