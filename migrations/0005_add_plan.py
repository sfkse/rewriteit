"""
Add plan column to users table
"""

from yoyo import step

steps = [
    step(
        """
        ALTER TABLE users ADD COLUMN plan VARCHAR(255) NOT NULL DEFAULT 'free'
        """,
        """
        ALTER TABLE users DROP COLUMN plan
        """
    )
] 