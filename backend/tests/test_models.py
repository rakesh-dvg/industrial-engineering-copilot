import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.roles import OrganizationRole
from app.models import Organization, OrganizationMember, User


@pytest.mark.asyncio
async def test_organization_user_membership(db_session: AsyncSession) -> None:
    organization = Organization(name="Acme Controls", slug="acme-controls")
    user = User(email="engineer@acme.example", display_name="Alex Engineer")
    membership = OrganizationMember(
        organization=organization,
        user=user,
        role=OrganizationRole.ENGINEER,
    )

    db_session.add_all([organization, user, membership])
    await db_session.commit()

    result = await db_session.execute(
        select(Organization).where(Organization.slug == "acme-controls")
    )
    stored_org = result.scalar_one()
    assert stored_org.name == "Acme Controls"
    assert len(stored_org.members) == 1
    assert stored_org.members[0].role == OrganizationRole.ENGINEER
