from yoyo import step

__depends__ = {'0008_restructure_user_table'}

steps = [
    step(
        """
        ALTER TABLE users ALTER COLUMN slack_user_id DROP NOT NULL;
        """,
        """
        ALTER TABLE users ALTER COLUMN slack_user_id SET NOT NULL;
        """
    )
] 