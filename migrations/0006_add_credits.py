"""
Add credits_assigned and credits_used columns to users table
"""

from yoyo import step

steps = [
    step(
        """
        ALTER TABLE users ADD COLUMN credits_assigned INT NOT NULL DEFAULT 0
        """,
        """
        ALTER TABLE users DROP COLUMN credits_assigned
        """
    ),
    step(
        """
        ALTER TABLE users ADD COLUMN credits_used INT NOT NULL DEFAULT 0
        """,
        """
        ALTER TABLE users DROP COLUMN credits_used
        """
    )
] 