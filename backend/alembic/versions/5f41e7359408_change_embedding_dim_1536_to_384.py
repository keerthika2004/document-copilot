"""change_embedding_dim_1536_to_384

Revision ID: 5f41e7359408
Revises: 6b1a34c39382
Create Date: 2026-07-07 22:23:04.747981

"""
import pgvector
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = '5f41e7359408'
down_revision: Union[str, Sequence[str], None] = '6b1a34c39382'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop indexes that reference the old vector dimension
    op.drop_index(op.f('ix_document_chunks_embedding_hnsw'), table_name='document_chunks', postgresql_ops={'embedding': 'vector_cosine_ops'}, postgresql_using='hnsw')

    # Change vector column from 1536 to 384 dimensions
    op.alter_column('document_chunks', 'embedding',
               existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=1536),
               type_=pgvector.sqlalchemy.vector.VECTOR(dim=384),
               existing_nullable=True)

    # Recreate HNSW index with new dimension
    op.create_index(op.f('ix_document_chunks_embedding_hnsw'), 'document_chunks', ['embedding'], unique=False, postgresql_ops={'embedding': 'vector_cosine_ops'}, postgresql_using='hnsw')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_document_chunks_embedding_hnsw'), table_name='document_chunks', postgresql_ops={'embedding': 'vector_cosine_ops'}, postgresql_using='hnsw')

    op.alter_column('document_chunks', 'embedding',
               existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=384),
               type_=pgvector.sqlalchemy.vector.VECTOR(dim=1536),
               existing_nullable=True)

    op.create_index(op.f('ix_document_chunks_embedding_hnsw'), 'document_chunks', ['embedding'], unique=False, postgresql_ops={'embedding': 'vector_cosine_ops'}, postgresql_using='hnsw')
