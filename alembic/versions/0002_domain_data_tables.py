"""create domain data tables"""

from alembic import op
import sqlalchemy as sa

revision = "0002_domain_data_tables"
down_revision = "0001_auth_orgs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_code", sa.String(length=64), nullable=False),
        sa.Column("industry", sa.String(length=128), nullable=False),
        sa.Column("host_count", sa.Integer(), nullable=False),
        sa.Column("threat_code", sa.Integer(), nullable=False),
        sa.Column("success", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(length=255), nullable=False),
        sa.Column("incident_date", sa.DateTime(), nullable=True),
        sa.Column("regional_time", sa.DateTime(), nullable=True),
        sa.Column("hour", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(length=16), nullable=False),
        sa.Column("time_of_day", sa.String(length=16), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
    )
    op.create_index("ix_incidents_id", "incidents", ["id"])
    op.create_index("ix_incidents_organization_code", "incidents", ["organization_code"])
    op.create_index("ix_incidents_industry", "incidents", ["industry"])
    op.create_index("ix_incidents_threat_code", "incidents", ["threat_code"])
    op.create_index("ix_incidents_region", "incidents", ["region"])
    op.create_index("ix_incidents_hour", "incidents", ["hour"])
    op.create_index("ix_incidents_season", "incidents", ["season"])
    op.create_index("ix_incidents_time_of_day", "incidents", ["time_of_day"])
    op.create_index("ix_incidents_day_of_week", "incidents", ["day_of_week"])

    op.create_table(
        "fstec_threats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("threat_code", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_characteristics", sa.Text(), nullable=True),
        sa.Column("object_of_impact", sa.Text(), nullable=True),
        sa.Column("confidentiality_breach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("integrity_breach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("availability_breach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("date_added", sa.DateTime(), nullable=True),
        sa.Column("last_modified", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_fstec_threats_id", "fstec_threats", ["id"])
    op.create_index("ix_fstec_threats_threat_code", "fstec_threats", ["threat_code"], unique=True)

    op.create_table(
        "organization_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=False),
        sa.Column("industry", sa.String(length=64), nullable=False),
        sa.Column("host_count", sa.Integer(), nullable=False),
        sa.Column("technologies", sa.Text(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_organization_settings_id", "organization_settings", ["id"])
    op.create_index(
        "ix_organization_settings_organization_id",
        "organization_settings",
        ["organization_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_organization_settings_organization_id", table_name="organization_settings")
    op.drop_index("ix_organization_settings_id", table_name="organization_settings")
    op.drop_table("organization_settings")

    op.drop_index("ix_fstec_threats_threat_code", table_name="fstec_threats")
    op.drop_index("ix_fstec_threats_id", table_name="fstec_threats")
    op.drop_table("fstec_threats")

    op.drop_index("ix_incidents_day_of_week", table_name="incidents")
    op.drop_index("ix_incidents_time_of_day", table_name="incidents")
    op.drop_index("ix_incidents_season", table_name="incidents")
    op.drop_index("ix_incidents_hour", table_name="incidents")
    op.drop_index("ix_incidents_region", table_name="incidents")
    op.drop_index("ix_incidents_threat_code", table_name="incidents")
    op.drop_index("ix_incidents_industry", table_name="incidents")
    op.drop_index("ix_incidents_organization_code", table_name="incidents")
    op.drop_index("ix_incidents_id", table_name="incidents")
    op.drop_table("incidents")
