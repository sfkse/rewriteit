"""
Add user_info JSON column to users table
"""

from yoyo import step

steps = [
    step(
        """
        ALTER TABLE users ADD COLUMN user_info JSONB
        """,
        """
        ALTER TABLE users DROP COLUMN user_info
        """
    )
] 