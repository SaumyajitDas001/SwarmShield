"""persist evaluator decisions"""
from alembic import op
from app.models import EvaluationRecord

revision = "0003_evaluations"
down_revision = "0002_attempts_observations"
branch_labels = None
depends_on = None


def upgrade():
    EvaluationRecord.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade():
    EvaluationRecord.__table__.drop(bind=op.get_bind(), checkfirst=True)
