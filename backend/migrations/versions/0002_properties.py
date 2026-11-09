"""Biens, photos locales et historique."""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "photos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "properties",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("address", sa.String(500)),
        sa.Column("city", sa.String(150)),
        sa.Column("surface", sa.Float),
        sa.Column("dpe", sa.String(1)),
        sa.Column("energy", sa.Float),
        sa.Column("ges", sa.String(1)),
        sa.Column("emissions", sa.Float),
        sa.Column("source", sa.String(30)),
        sa.Column("agency", sa.String(200)),
        sa.Column("notes", sa.Text),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("next_action", sa.Date),
        sa.Column("photo_id", sa.String(36), sa.ForeignKey("photos.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted", sa.Boolean, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.CheckConstraint("surface IS NULL OR surface >= 0", name="ck_surface"),
        sa.CheckConstraint("energy IS NULL OR energy >= 0", name="ck_energy"),
        sa.CheckConstraint("emissions IS NULL OR emissions >= 0", name="ck_emissions"),
        sa.CheckConstraint(
            "dpe IS NULL OR dpe IN ('A','B','C','D','E','F','G')", name="ck_dpe"
        ),
        sa.CheckConstraint(
            "ges IS NULL OR ges IN ('A','B','C','D','E','F','G')", name="ck_ges"
        ),
        sa.CheckConstraint(
            "source IS NULL OR source IN ('Registre DPE','Agence immobilière')",
            name="ck_source",
        ),
        sa.CheckConstraint(
            "status IN ('Non prospecté','Prospection prévue','Prospection impossible','Prospecté')",
            name="ck_status",
        ),
        sa.CheckConstraint("version >= 1", name="ck_version"),
    )
    for field in ["status", "created_at", "deleted"]:
        op.create_index(f"ix_properties_{field}", "properties", [field])
    op.create_table(
        "property_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=False
        ),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snapshot", sa.JSON, nullable=False),
    )
    op.create_index(
        "ix_property_history_property_id", "property_history", ["property_id"]
    )


def downgrade():
    # An explicit migration downgrade is a developer operation, never run by the launcher.
    op.drop_table("property_history")
    op.drop_table("properties")
    op.drop_table("photos")
