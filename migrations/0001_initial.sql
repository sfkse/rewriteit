-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    slack_user_id VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create paraphrases table
CREATE TABLE IF NOT EXISTS paraphrases (
    id SERIAL PRIMARY KEY,
    original_text TEXT NOT NULL,
    paraphrased_text TEXT NOT NULL,
    tone VARCHAR,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index on slack_user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_slack_user_id ON users(slack_user_id);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_paraphrases_user_id ON paraphrases(user_id);

-- Create index on created_at for faster sorting
CREATE INDEX IF NOT EXISTS idx_paraphrases_created_at ON paraphrases(created_at);
