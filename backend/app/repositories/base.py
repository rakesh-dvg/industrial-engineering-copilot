from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


class OrganizationScopedRepository(BaseRepository):
    """Base class for repositories that enforce tenant isolation."""

    def __init__(self, session: AsyncSession, organization_id: UUID | None = None) -> None:
        super().__init__(session)
        self.organization_id = organization_id
