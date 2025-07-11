"""Add hash

Revision ID: 0340cb4673d3
Revises: 0cce2f7085ef
Create Date: 2025-07-04 02:29:35.220329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0340cb4673d3'
down_revision: Union[str, Sequence[str], None] = '0cce2f7085ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('description_hash', sa.String(length=32), nullable=False))
    op.drop_constraint(op.f('uq_event_title_description'), 'events', type_='unique')
    op.create_index(op.f('ix_events_description_hash'), 'events', ['description_hash'], unique=False)
    op.create_unique_constraint('uq_event_title_description_hash', 'events', ['title', 'description_hash'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('uq_event_title_description_hash', 'events', type_='unique')
    op.drop_index(op.f('ix_events_description_hash'), table_name='events')
    op.create_unique_constraint(op.f('uq_event_title_description'), 'events', ['title', 'description'], postgresql_nulls_not_distinct=False)
    op.drop_column('events', 'description_hash')
    # ### end Alembic commands ###
