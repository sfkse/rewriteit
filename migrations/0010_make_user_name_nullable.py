from yoyo import step

__depends__ = {'0009_make_slack_user_id_nullable'}

steps = [
    step(
        """
        ALTER TABLE users ALTER COLUMN user_name DROP NOT NULL;
        """,
        """
        ALTER TABLE users ALTER COLUMN user_name SET NOT NULL;
        """
    )
] 