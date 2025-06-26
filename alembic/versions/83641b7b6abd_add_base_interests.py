"""add base interests

Revision ID: 83641b7b6abd
Revises: 7ee097a4c912
Create Date: 2025-06-26 19:35:55.909184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83641b7b6abd'
down_revision: Union[str, Sequence[str], None] = '7ee097a4c912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    interests_list = [
        "Music",
        "Art",
        "Sports",
        "Technology",
        "Food & Drink",
        "Travel",
        "Health & Fitness",
        "Movies",
        "Theater",
        "Networking",
        "Photography",
        "Fashion",
        "Gaming",
        "Science",
        "Education",
        "Outdoors",
        "Literature",
        "Dance",
        "Charity",
        "Workshops",
        "Yoga",
        "Meditation",
        "Startups",
        "Business",
        "Comedy",
        "History",
        "Cars",
        "Environment",
        "Politics",
        "Cultural Events",
        "Family",
        "Kids Activities",
        "Festivals",
        "Conferences",
        "Crafts",
        "DIY",
        "Wine Tasting",
        "Language Learning",
        "Writing",
        "Social Causes"
    ]
    stmt = sa.text("INSERT INTO interests (name) VALUES (:name) ON CONFLICT DO NOTHING").bindparams(
        sa.bindparam("name", type_=sa.String()))
    for name in interests_list:
        op.execute(stmt.params(name=name))


def downgrade() -> None:
    """Downgrade schema."""
    pass
