from enum import StrEnum


class OrganizationRole(StrEnum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    SALES = "sales"
    REVIEWER = "reviewer"
    VIEWER = "viewer"
