"""persist normalized validation attempts and observations"""
from alembic import op
from app.models import AttackAttemptRecord, ObservationRecord

revision = "0002_attempts_observations"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    AttackAttemptRecord.__table__.create(bind=op.get_bind(), checkfirst=True)
    ObservationRecord.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade():
    ObservationRecord.__table__.drop(bind=op.get_bind(), checkfirst=True)
    AttackAttemptRecord.__table__.drop(bind=op.get_bind(), checkfirst=True)
