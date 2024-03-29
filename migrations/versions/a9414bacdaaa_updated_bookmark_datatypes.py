"""Updated Bookmark datatypes

Revision ID: a9414bacdaaa
Revises: 0c0ceb2a2123
Create Date: 2021-05-27 22:50:55.875207

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a9414bacdaaa'
down_revision = '0c0ceb2a2123'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('bookmarks', 'id',
               existing_type=mysql.INTEGER(display_width=11),
               type_=mysql.INTEGER(unsigned=True),
               existing_nullable=False)
    op.alter_column('bookmarks', 'zoom',
               existing_type=mysql.SMALLINT(display_width=6),
               type_=mysql.TINYINT(unsigned=True),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('bookmarks', 'zoom',
               existing_type=mysql.TINYINT(unsigned=True),
               type_=mysql.SMALLINT(display_width=6),
               existing_nullable=False)
    op.alter_column('bookmarks', 'id',
               existing_type=mysql.INTEGER(unsigned=True),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=False)
    # ### end Alembic commands ###
