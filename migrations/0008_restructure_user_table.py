"""
Restructure user table: remove credits columns and add email column
"""

from yoyo import step

__depends__ = {'0007_add_user_info'}

steps = [
    step(
        """
        ALTER TABLE users DROP COLUMN IF EXISTS credits_assigned;
        ALTER TABLE users DROP COLUMN IF EXISTS credits_used;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;
        """,
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_assigned INT NOT NULL DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_used INT NOT NULL DEFAULT 0;
        ALTER TABLE users DROP COLUMN IF EXISTS email;
        """
    )
] 