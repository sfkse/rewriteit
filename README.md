# SlackParaphrase

A Slack bot that helps rephrase messages using OpenRouter API. The bot can paraphrase text with different tones while maintaining the original meaning.

## Features

- OAuth-based Slack app installation
- Message paraphrasing with customizable tones
- PostgreSQL database for storing user data and paraphrase history
- Secure handling of API keys and tokens
- SSL support for secure communication

## Prerequisites

- Docker and Docker Compose
- SSL certificates (for HTTPS)
- Slack App credentials
- OpenRouter API key

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Project Structure

```
slackparaphrase/
├── src/
│   ├── models/
│   │   ├── database.py    # Database models
│   │   ├── paraphrase.py  # Paraphrase-related models
│   │   └── slack.py       # Slack-related models
│   ├── routes/
│   │   ├── oauth.py       # OAuth endpoint handlers
│   │   └── rephrase.py    # Rephrase endpoint handlers
│   ├── services/
│   │   ├── database.py    # Database operations
│   │   └── paraphrase.py  # Paraphrasing service
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection
│   └── main.py           # FastAPI application
├── migrations/           # Database migrations
├── certs/               # SSL certificates
├── docker-compose.yml   # Docker services configuration
├── Dockerfile          # Application container definition
└── requirements.txt    # Python dependencies
```

## Database Migrations

The project uses Yoyo migrations for database schema management. Migrations are automatically applied when the application starts.

Migration files are located in the `migrations/` directory:

- `0001_initial.sql`: Creates users and paraphrases tables

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

2. Run the application locally:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile ./certs/key.pem --ssl-certfile ./certs/cert.pem
   ```

## Database Management

The application uses PostgreSQL for data storage. To connect to the database:

```bash
psql -h localhost -U postgres -d slackparaphrase
```

Default database configuration:

- Host: localhost
- Port: 5432
- Database: slackparaphrase
- Username: postgres
- Password: postgres

## Slack App Configuration

1. Create a Slack App at https://api.slack.com/apps
2. Configure OAuth & Permissions:
   - Add redirect URL: `https://your-domain:8443/oauth`
   - Required scopes:
     - `chat:write`
     - `chat:write.public`
     - `commands`
     - `channels:history`
     - `groups:history`
     - `mpim:history`
     - `im:history`
3. Install the app to your workspace

## License

[MIT License](LICENSE)

