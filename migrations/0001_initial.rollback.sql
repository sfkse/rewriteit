-- Drop indexes first
DROP INDEX IF EXISTS idx_paraphrases_created_at;
DROP INDEX IF EXISTS idx_paraphrases_user_id;
DROP INDEX IF EXISTS idx_users_slack_user_id;

-- Drop tables
DROP TABLE IF EXISTS paraphrases;
DROP TABLE IF EXISTS users; 