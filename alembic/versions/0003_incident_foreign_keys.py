"""Link incidents to organizations and FSTEC threats (FK + backfill)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0003_incident_foreign_keys"
down_revision = "0002_domain_data_tables"
branch_labels = None
depends_on = None


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def upgrade() -> None:
    if _is_sqlite():
        with op.batch_alter_table("incidents") as batch_op:
            batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
    else:
        op.add_column("incidents", sa.Column("organization_id", sa.Integer(), nullable=True))

    conn = op.get_bind()

    conn.execute(
        text("""
            UPDATE incidents
            SET organization_id = (
                SELECT organizations.id FROM organizations
                WHERE organizations.code = incidents.organization_code
            )
        """)
    )

    conn.execute(
        text("""
            INSERT INTO organizations (name, code)
            SELECT DISTINCT
                'Organization ' || incidents.organization_code,
                incidents.organization_code
            FROM incidents
            WHERE incidents.organization_id IS NULL
              AND incidents.organization_code IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM organizations o WHERE o.code = incidents.organization_code
              )
        """)
    )

    conn.execute(
        text("""
            UPDATE incidents
            SET organization_id = (
                SELECT organizations.id FROM organizations
                WHERE organizations.code = incidents.organization_code
            )
            WHERE incidents.organization_id IS NULL
        """)
    )

    null_text = "CAST(NULL AS TEXT)"
    null_ts = "CAST(NULL AS TIMESTAMP)"
    if _is_sqlite():
        status_null = null_text
    else:
        status_null = "CAST(NULL AS VARCHAR(128))"
    conn.execute(
        text(f"""
            INSERT INTO fstec_threats (
                threat_code, name, description,
                source_characteristics, object_of_impact,
                confidentiality_breach, integrity_breach, availability_breach,
                date_added, last_modified, status, notes
            )
            SELECT DISTINCT
                i.threat_code,
                'Threat ' || CAST(i.threat_code AS TEXT),
                'Placeholder row created for referential integrity.',
                {null_text}, {null_text}, 0, 0, 0,
                {null_ts}, {null_ts}, {status_null}, {null_text}
            FROM incidents i
            WHERE NOT EXISTS (
                SELECT 1 FROM fstec_threats f WHERE f.threat_code = i.threat_code
            )
        """)
    )

    if _is_sqlite():
        with op.batch_alter_table("incidents") as batch_op:
            batch_op.alter_column("organization_id", existing_type=sa.Integer(), nullable=False)
            batch_op.create_foreign_key(
                "fk_incidents_organization_id",
                "organizations",
                ["organization_id"],
                ["id"],
                ondelete="RESTRICT",
            )
            batch_op.create_foreign_key(
                "fk_incidents_threat_code",
                "fstec_threats",
                ["threat_code"],
                ["threat_code"],
                ondelete="RESTRICT",
            )
    else:
        op.alter_column("incidents", "organization_id", existing_type=sa.Integer(), nullable=False)
        op.create_foreign_key(
            "fk_incidents_organization_id",
            "incidents",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        op.create_foreign_key(
            "fk_incidents_threat_code",
            "incidents",
            "fstec_threats",
            ["threat_code"],
            ["threat_code"],
            ondelete="RESTRICT",
        )

    op.create_index(
        "ix_incidents_organization_id_season_region",
        "incidents",
        ["organization_id", "season", "region"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_incidents_organization_id_season_region", table_name="incidents")
    if _is_sqlite():
        with op.batch_alter_table("incidents") as batch_op:
            batch_op.drop_constraint("fk_incidents_threat_code", type_="foreignkey")
            batch_op.drop_constraint("fk_incidents_organization_id", type_="foreignkey")
            batch_op.drop_column("organization_id")
    else:
        op.drop_constraint("fk_incidents_threat_code", "incidents", type_="foreignkey")
        op.drop_constraint("fk_incidents_organization_id", "incidents", type_="foreignkey")
        op.drop_column("incidents", "organization_id")
