from mongoengine import StringField, BinaryField
import bcrypt
from cryptography.fernet import Fernet
import base64
import hashlib


class HashedValue:
    def __init__(self, hashed_value: str):
        self.hashed_value = hashed_value

    def verify(self, plain_text: str) -> bool:
        """Verify the plain text against the hashed value."""
        if self.hashed_value is None:
            return False
        return bcrypt.checkpw(
            plain_text.encode("utf-8"), self.hashed_value.encode("utf-8")
        )


class HashedField(StringField):
    def __init__(self, *args, **kwargs):
        self.rounds = kwargs.pop("rounds", 12)
        self.custom_salt = kwargs.pop("salt", None)
        super().__init__(*args, **kwargs)

    def to_mongo(self, value: str) -> str | None:
        """Hash the value before saving to MongoDB."""
        if value is not None and not value.startswith("$2b$"):
            # Hash the value using bcrypt
            salt = (
                self.custom_salt.encode("utf-8")
                if self.custom_salt
                else bcrypt.gensalt(self.rounds)
            )
            hashed_value = bcrypt.hashpw(value.encode("utf-8"), salt)
            return hashed_value.decode("utf-8")
        return value

    def __get__(self, instance, owner) -> HashedValue:
        """Return a HashedValue instance for verification."""
        stored_hash = instance._data.get(self.name) if instance else None
        return HashedValue(stored_hash)


class EncryptedField(BinaryField):
    def __init__(self, key: str | bytes = None, key_lambda=None, *args, **kwargs):
        """
        EncryptedField with dynamic key support.

        :param key: Optional global key for encryption.
        :param key_lambda: Lambda function to derive a key from the instance.
        """
        # If key is string, convert to bytes
        if isinstance(key, str):
            key = key.encode("utf-8")

        if key and key_lambda:
            raise ValueError("Cannot use both 'key' and 'key_lambda'. Choose one.")

        # Static key support
        self.global_key = self._derive_key(key) if key else None
        self.key_lambda = key_lambda

        super().__init__(*args, **kwargs)

    @staticmethod
    def _derive_key(key: bytes) -> bytes:
        """Derive a Fernet-compatible key."""
        # Hash the key to ensure it's 32 bytes for Fernet
        hashed_key = hashlib.sha256(key).digest()
        return base64.urlsafe_b64encode(hashed_key)

    def _get_cipher(self, instance):
        """Retrieve the Fernet cipher using the appropriate key."""
        if self.key_lambda:
            key = self.key_lambda(instance)
            if not key:
                raise ValueError("Encryption key not provided.")
            key = self._derive_key(key)
        else:
            if not self.global_key:
                raise ValueError("Global encryption key not provided.")
            key = self.global_key

        return Fernet(key)

    def to_mongo(self, value: str) -> bytes:
        """Encrypt the value before saving to MongoDB."""
        if value is not None:
            cipher = self._get_cipher(self.instance)
            encrypted_value = cipher.encrypt(value.encode("utf-8"))
            return encrypted_value

    def from_mongo(self, value: bytes) -> str:
        """Decrypt the value when loading from MongoDB."""
        if value is not None:
            cipher = self._get_cipher(self.instance)
            decrypted_value = cipher.decrypt(value)
            return decrypted_value.decode("utf-8")

    def __set__(self, instance, value):
        """Encrypt the value before storing."""
        self.instance = instance
        if value:
            encrypted_value = self.to_mongo(value)
            instance._data[self.name] = encrypted_value

    def __get__(self, instance, owner):
        """Decrypt the value when accessed."""
        if not instance:
            return self
        encrypted_value = instance._data.get(self.name)
        if encrypted_value:
            return self.from_mongo(encrypted_value)
        return None
