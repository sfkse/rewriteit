"""
Create initial tables for users and paraphrases
"""

from yoyo import step

steps = [
    step(
        """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            slack_user_id VARCHAR NOT NULL UNIQUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        DROP TABLE users
        """
    ),
    step(
        """
        CREATE TABLE paraphrases (
            id SERIAL PRIMARY KEY,
            original_text TEXT NOT NULL,
            paraphrased_text TEXT NOT NULL,
            tone VARCHAR,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        DROP TABLE paraphrases
        """
    ),
    step(
        """
        CREATE INDEX idx_users_slack_user_id ON users(slack_user_id)
        """,
        """
        DROP INDEX idx_users_slack_user_id
        """
    ),
    step(
        """
        CREATE INDEX idx_paraphrases_user_id ON paraphrases(user_id)
        """,
        """
        DROP INDEX idx_paraphrases_user_id
        """
    ),
    step(
        """
        CREATE INDEX idx_paraphrases_created_at ON paraphrases(created_at)
        """,
        """
        DROP INDEX idx_paraphrases_created_at
        """
    )
] 