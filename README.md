# RewordIt

A Slack bot that helps rephrase messages using OpenRouter API. The bot can paraphrase text with different tones while maintaining the original meaning.

## Features

- OAuth-based Slack app installation
- Message paraphrasing with customizable tones
- PostgreSQL database with UUID primary keys
- Secure handling of API keys and tokens
- SSL support for secure communication
- Background task processing for Slack's 3-second timeout
- Automatic database migrations

## Prerequisites

- Docker and Docker Compose
- SSL certificates (for HTTPS)
- Slack App credentials
- OpenRouter API key

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Slack Configuration
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_API_BASE_URL=https://slack.com/api

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-3.5-turbo
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@slackparaphrase-db:5433/slackparaphrase
DB_PORT=5433

# API Configuration
API_PORT=8443
API_BASE_URL=https://your-domain.com
USE_SSL=true

# SSL Configuration
SSL_CERT_PATH=/app/certs/cert.pem
SSL_KEY_PATH=/app/certs/key.pem
```

## Project Structure

```
slackparaphrase/
├── src/
│   ├── models/
│   │   ├── database.py    # Database models (User, Paraphrase)
│   │   ├── paraphrase.py  # Paraphrase-related models
│   │   └── slack.py       # Slack-related models
│   ├── routes/
│   │   ├── oauth.py       # OAuth endpoint handlers
│   │   └── rephrase.py    # Rephrase endpoint handlers
│   ├── services/
│   │   ├── database.py    # Database operations
│   │   ├── paraphrase.py  # Paraphrasing service
│   │   └── slack.py       # Slack service
│   ├── utils/
│   │   ├── auth.py        # Authentication utilities
│   │   ├── layout.py      # Slack message layouts
│   │   └── text.py        # Text processing utilities
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection
│   └── main.py           # FastAPI application
├── migrations/           # Database migrations
│   ├── 0001_initial.py  # Initial tables
│   ├── 0002_uuid_columns copy.py  # UUID conversion
│   ├── 0003_add_user_name.py  # Add user_name column
│   └── 0004_add_paraphrase_updated_at.py  # Add updated_at column
├── certs/               # SSL certificates
├── docker-compose.yml   # Docker services configuration
├── Dockerfile          # Application container definition
└── requirements.txt    # Python dependencies
```

## Database Migrations

The project uses Yoyo migrations for database schema management. Migrations are automatically applied when the application starts.

Current migrations:

- `0001_initial.py`: Creates initial users and paraphrases tables
- `0002_uuid_columns copy.py`: Converts ID columns to UUID type
- `0003_add_user_name.py`: Adds user_name column to users table
- `0004_add_paraphrase_updated_at.py`: Adds updated_at column to paraphrases table

## Running the Application

1. Generate SSL certificates and place them in the `certs/` directory:

   ```bash
   mkdir certs
   openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365
   ```

2. Start the application using Docker Compose:
   ```bash
   docker compose up --build
   ```

The application will be available at `https://localhost:8443`.

## Development

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Generate SSL certificates and place them in the `certs/` directory:

   ```bash
   mkdir certs
   openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365
   ```

3. Run the application locally:

   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile ./certs/key.pem --ssl-certfile ./certs/cert.pem
   ```

## Database Management

The application uses PostgreSQL for data storage. To connect to the database:

```bash
psql -h localhost -p 5433 -U postgres -d slackparaphrase
```

Default database configuration:

- Host: localhost
- Port: 5433
- User: postgres
- Password: postgres
- Database: slackparaphrase

## Usage

1. Install the Slack app in your workspace
2. Use the `/reword` command followed by your text:
   ```
   /reword Hello, how are you today?
   ```
3. Optionally specify a tone:
   ```
   /reword --tone formal Hello, how are you today?
   ```
4. Use the "Rewrite" button to get a new paraphrase
5. Use the "Copy" button to copy the paraphrased text

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)

