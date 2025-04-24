"""Add language to PresentationFile

Revision ID: 18b343b83512
Revises: a684ebcf87f2
Create Date: 2025-01-22 09:47:14.050893

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '18b343b83512'
down_revision: Union[str, None] = 'a684ebcf87f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns with nullable=True initially
    op.add_column('presentation_files', sa.Column('uuid', sa.String(), nullable=True))
    op.add_column('presentation_files', sa.Column('stage_number', sa.Integer(), nullable=True))
    op.add_column('presentation_files', sa.Column('stage_text', sa.Text(), nullable=True))
    op.add_column('presentation_files', sa.Column('language', sa.String(), nullable=True))

    # Generate default values for existing rows
    connection = op.get_bind()
    presentation_files_table = sa.table(
        'presentation_files',
        sa.column('id', sa.Integer),
        sa.column('uuid', sa.String),
        sa.column('stage_number', sa.Integer),
        sa.column('language', sa.String),
    )

    # Update existing rows with default values
    rows = connection.execute(sa.select(presentation_files_table.c.id)).fetchall()
    for row in rows:
        connection.execute(
            presentation_files_table.update()
            .where(presentation_files_table.c.id == row.id)
            .values(
                uuid=str(uuid.uuid4()),  # Assign a unique UUID
                stage_number=3,  # Default stage number
                language='ru',  # Default language
            )
        )

    # Alter columns to set them as NOT NULL
    op.alter_column('presentation_files', 'uuid', nullable=False)
    op.alter_column('presentation_files', 'stage_number', nullable=False)
    op.alter_column('presentation_files', 'language', nullable=False)

    # Add unique constraint for the UUID column
    op.create_unique_constraint(None, 'presentation_files', ['uuid'])


def downgrade() -> None:
    # Drop constraints and columns
    op.drop_constraint(None, 'presentation_files', type_='unique')
    op.drop_column('presentation_files', 'language')
    op.drop_column('presentation_files', 'stage_text')
    op.drop_column('presentation_files', 'stage_number')
    op.drop_column('presentation_files', 'uuid')
