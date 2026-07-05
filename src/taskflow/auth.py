"""Authentication and authorization for multi-tenant TaskFlow."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


# Role hierarchy — higher index = more permissions
ROLES = ("viewer", "operator", "admin")

# Permission matrix
PERMISSIONS: dict[str, list[str]] = {
    "viewer": ["tasks.read", "pipelines.read", "metrics.read"],
    "operator": ["tasks.read", "tasks.write", "tasks.cancel", "pipelines.read", "pipelines.run", "metrics.read"],
    "admin": [
        "tasks.read", "tasks.write", "tasks.cancel", "tasks.delete",
        "pipelines.read", "pipelines.write", "pipelines.run", "pipelines.delete",
        "users.read", "users.write", "settings.read", "settings.write",
        "metrics.read",
    ],
}

# API key settings
API_KEY_LENGTH = 32
API_KEY_PREFIX = "tf_"
SESSION_TTL_SECONDS = 3600


class User:
    """Represents an authenticated user with role-based permissions."""

    def __init__(self, username: str, role: str = "viewer", workspace: str = "default") -> None:
        if role not in ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {ROLES}")
        self.username = username
        self.role = role
        self.workspace = workspace

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in PERMISSIONS.get(self.role, [])

    def can_access_workspace(self, workspace: str) -> bool:
        """Check if user can access a workspace."""
        if self.role == "admin":
            return True
        return self.workspace == workspace

    def to_dict(self) -> dict[str, str]:
        return {
            "username": self.username,
            "role": self.role,
            "workspace": self.workspace,
        }


class APIKeyManager:
    """Manages API key generation, hashing, and validation.

    API keys are stored as HMAC-SHA256 hashes. The raw key is only
    shown once at creation time and cannot be recovered.

    Key format: tf_<32 random hex chars>
    """

    def __init__(self, secret: str = "default-secret") -> None:
        self._secret = secret.encode()
        self._keys: dict[str, dict[str, Any]] = {}  # hash -> user info

    def generate_key(self, username: str, role: str = "operator") -> str:
        """Generate a new API key for a user. Returns the raw key (show once)."""
        raw_key = f"{API_KEY_PREFIX}{secrets.token_hex(API_KEY_LENGTH)}"
        key_hash = self._hash_key(raw_key)

        self._keys[key_hash] = {
            "username": username,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return raw_key

    def validate_key(self, raw_key: str) -> User | None:
        """Validate an API key and return the associated user."""
        if not raw_key.startswith(API_KEY_PREFIX):
            return None

        key_hash = self._hash_key(raw_key)
        info = self._keys.get(key_hash)
        if info is None:
            return None

        return User(username=info["username"], role=info["role"])

    def revoke_key(self, raw_key: str) -> bool:
        """Revoke an API key. Returns True if found and revoked."""
        key_hash = self._hash_key(raw_key)
        if key_hash in self._keys:
            del self._keys[key_hash]
            return True
        return False

    def _hash_key(self, raw_key: str) -> str:
        """Create a deterministic hash of an API key."""
        return hmac.new(self._secret, raw_key.encode(), hashlib.sha256).hexdigest()

    def list_keys(self) -> list[dict[str, str]]:
        """List all registered keys (without the raw key values)."""
        return [
            {"username": info["username"], "role": info["role"], "created_at": info["created_at"]}
            for info in self._keys.values()
        ]


class SessionManager:
    """Manages user sessions with expiration.

    Sessions are short-lived tokens created after API key validation.
    They reduce the need to validate the full API key on every request.
    """

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, user: User) -> str:
        """Create a new session for a user. Returns session token."""
        token = secrets.token_urlsafe(32)
        self._sessions[token] = {
            "user": user.to_dict(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds)).isoformat(),
        }
        return token

    def validate_session(self, token: str) -> User | None:
        """Validate a session token. Returns user if valid and not expired."""
        session = self._sessions.get(token)
        if session is None:
            return None

        expires = datetime.fromisoformat(session["expires_at"])
        if datetime.now(timezone.utc) > expires:
            del self._sessions[token]
            return None

        info = session["user"]
        return User(username=info["username"], role=info["role"], workspace=info["workspace"])

    def revoke_session(self, token: str) -> bool:
        """Revoke a session. Returns True if found."""
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count removed."""
        now = datetime.now(timezone.utc)
        expired = [
            token for token, session in self._sessions.items()
            if datetime.fromisoformat(session["expires_at"]) < now
        ]
        for token in expired:
            del self._sessions[token]
        return len(expired)
