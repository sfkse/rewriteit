"""
Add user_name column to users table
"""

from yoyo import step

steps = [
    step(
        """
        ALTER TABLE users ADD COLUMN user_name VARCHAR NOT NULL DEFAULT ''
        """,
        """
        ALTER TABLE users DROP COLUMN user_name
        """
    )
] 