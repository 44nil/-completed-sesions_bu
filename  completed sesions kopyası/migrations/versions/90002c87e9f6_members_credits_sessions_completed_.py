"""members.credits + sessions.completed + statuses

Revision ID: 90002c87e9f6
Revises:
Create Date: 2025-08-09 16:17:37.488508
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '90002c87e9f6'
down_revision = '6646b5f6fb56'
branch_labels = None
depends_on = None


def _table_exists(insp, name: str) -> bool:
    return name in insp.get_table_names()


def _column_exists(insp, table: str, column: str) -> bool:
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    # 1) members.credits (>= 0, default 0)
    if _table_exists(insp, "members") and not _column_exists(insp, "members", "credits"):
        op.add_column(
            "members",
            sa.Column("credits", sa.Integer(), nullable=False, server_default="0"),
        )
        # Non-negative check (best-effort; SQLite isimli CHECK'lerde sorun çıkarabilir)
        try:
            op.create_check_constraint(
                "ck_members_credits_nonnegative", "members", "credits >= 0"
            )
        except Exception:
            pass  # zaten varsa / desteklemiyorsa

    # 2) sessions.completed (bool)
    if _table_exists(insp, "sessions") and not _column_exists(insp, "sessions", "completed"):
        server_default = sa.text("false") if dialect != "sqlite" else "0"
        op.add_column(
            "sessions",
            sa.Column("completed", sa.Boolean(), nullable=False, server_default=server_default),
        )

    # 3) bookings.status (ENUM) + bookings.attended_at (opt-in: tablo varsa)
    if _table_exists(insp, "bookings"):
        # status
        if not _column_exists(insp, "bookings", "status"):
            if dialect == "postgresql":
                # Create ENUM type if not exists
                op.execute(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'booking_status') THEN
                            CREATE TYPE booking_status AS ENUM (
                                'booked','confirmed','attended','canceled','no_show','waitlisted'
                            );
                        END IF;
                    END$$;
                    """
                )
                status_type = sa.Enum(
                    "booked", "confirmed", "attended", "canceled", "no_show", "waitlisted",
                    name="booking_status"
                )
            else:
                # Fallback for non-Postgres
                status_type = sa.String(length=20)

            op.add_column(
                "bookings",
                sa.Column("status", status_type, nullable=False, server_default="booked"),
            )
            op.create_index("ix_bookings_status", "bookings", ["status"])

        # attended_at (tamamlanma zamanı)
        if not _column_exists(insp, "bookings", "attended_at"):
            op.add_column(
                "bookings",
                sa.Column("attended_at", sa.DateTime(timezone=True), nullable=True),
            )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    # 3) bookings.*
    if _table_exists(insp, "bookings"):
        if _column_exists(insp, "bookings", "attended_at"):
            op.drop_column("bookings", "attended_at")

        if _column_exists(insp, "bookings", "status"):
            try:
                op.drop_index("ix_bookings_status", table_name="bookings")
            except Exception:
                pass
            op.drop_column("bookings", "status")
            if dialect == "postgresql":
                # ENUM'u temizle (başka kolonda kullanılmıyorsa)
                op.execute("DROP TYPE IF EXISTS booking_status;")

    # 2) sessions.completed
    if _table_exists(insp, "sessions") and _column_exists(insp, "sessions", "completed"):
        op.drop_column("sessions", "completed")

    # 1) members.credits
    if _table_exists(insp, "members") and _column_exists(insp, "members", "credits"):
        # CHECK constraint'i düşür
        try:
            op.drop_constraint("ck_members_credits_nonnegative", "members", type_="check")
        except Exception:
            pass
        op.drop_column("members", "credits")
