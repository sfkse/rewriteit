"""
Add updated_at column to paraphrases table
"""

from yoyo import step

steps = [
    step(
        """
        ALTER TABLE paraphrases ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        """,
        """
        ALTER TABLE paraphrases DROP COLUMN updated_at
        """
    )
] 