"""
Convert ID columns to UUID type
"""

from yoyo import step

steps = [
    step(
        """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
        """,
        """
        DROP EXTENSION IF EXISTS "uuid-ossp"
        """
    ),
    step(
        """
        ALTER TABLE users ADD COLUMN uuid UUID DEFAULT uuid_generate_v4()
        """,
        """
        ALTER TABLE users DROP COLUMN uuid
        """
    ),
    step(
        """
        ALTER TABLE paraphrases ADD COLUMN uuid UUID DEFAULT uuid_generate_v4()
        """,
        """
        ALTER TABLE paraphrases DROP COLUMN uuid
        """
    ),
    step(
        """
        ALTER TABLE paraphrases ADD COLUMN user_uuid UUID
        """,
        """
        ALTER TABLE paraphrases DROP COLUMN user_uuid
        """
    ),
    step(
        """
        UPDATE paraphrases p
        SET user_uuid = u.uuid
        FROM users u
        WHERE p.user_id = u.id
        """,
        """
        UPDATE paraphrases SET user_uuid = NULL
        """
    ),
    step(
        """
        ALTER TABLE paraphrases DROP CONSTRAINT paraphrases_user_id_fkey
        """,
        """
        ALTER TABLE paraphrases ADD CONSTRAINT paraphrases_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
        """
    ),
    step(
        """
        ALTER TABLE users DROP CONSTRAINT users_pkey
        """,
        """
        ALTER TABLE users ADD PRIMARY KEY (id)
        """
    ),
    step(
        """
        ALTER TABLE users DROP COLUMN id
        """,
        """
        ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY
        """
    ),
    step(
        """
        ALTER TABLE users RENAME COLUMN uuid TO id
        """,
        """
        ALTER TABLE users RENAME COLUMN id TO uuid
        """
    ),
    step(
        """
        ALTER TABLE users ADD PRIMARY KEY (id)
        """,
        """
        ALTER TABLE users DROP CONSTRAINT users_pkey
        """
    ),
    step(
        """
        ALTER TABLE paraphrases DROP CONSTRAINT paraphrases_pkey
        """,
        """
        ALTER TABLE paraphrases ADD PRIMARY KEY (id)
        """
    ),
    step(
        """
        ALTER TABLE paraphrases DROP COLUMN id
        """,
        """
        ALTER TABLE paraphrases ADD COLUMN id SERIAL PRIMARY KEY
        """
    ),
    step(
        """
        ALTER TABLE paraphrases RENAME COLUMN uuid TO id
        """,
        """
        ALTER TABLE paraphrases RENAME COLUMN id TO uuid
        """
    ),
    step(
        """
        ALTER TABLE paraphrases ADD PRIMARY KEY (id)
        """,
        """
        ALTER TABLE paraphrases DROP CONSTRAINT paraphrases_pkey
        """
    ),
    step(
        """
        ALTER TABLE paraphrases DROP COLUMN user_id
        """,
        """
        ALTER TABLE paraphrases ADD COLUMN user_id INTEGER REFERENCES users(id)
        """
    ),
    step(
        """
        ALTER TABLE paraphrases RENAME COLUMN user_uuid TO user_id
        """,
        """
        ALTER TABLE paraphrases RENAME COLUMN user_id TO user_uuid
        """
    ),
    step(
        """
        ALTER TABLE paraphrases ADD CONSTRAINT paraphrases_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
        """,
        """
        ALTER TABLE paraphrases DROP CONSTRAINT paraphrases_user_id_fkey
        """
    )
] 