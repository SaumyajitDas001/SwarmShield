"""persist campaign-scoped swarm discoveries"""
from alembic import op
from app.models import AgentMemoryRecord

revision = "0004_agent_memory"
down_revision = "0003_evaluations"
branch_labels = None
depends_on = None


def upgrade():
    AgentMemoryRecord.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade():
    AgentMemoryRecord.__table__.drop(bind=op.get_bind(), checkfirst=True)
