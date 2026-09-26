"""Authentication interfaces for future JWT and tenant isolation."""

from dataclasses import dataclass
from uuid import UUID

from app.auth.roles import OrganizationRole


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: UUID
    email: str
    display_name: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class OrganizationContext:
    organization_id: UUID
    role: OrganizationRole


@dataclass(frozen=True, slots=True)
class AuthContext:
    user: AuthenticatedUser
    organization: OrganizationContext | None = None
