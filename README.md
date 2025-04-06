# SlackParaphrase

A Slack application that rephrases text using the OpenRouter API and ChatGPT.

## Features

- Rephrase text using the OpenRouter API and ChatGPT
- Slack integration for easy access
- Docker support for easy deployment
- Code formatting with Black

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Slack workspace
- OpenRouter API key

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Running the Application

### Development Mode

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
uvicorn src.main:app --reload
```

### Docker

1. Build and run the application:

```bash
docker-compose up --build
```

## Code Formatting

This project uses [Black](https://github.com/psf/black) for code formatting. To format the code:

```bash
black .
```

To install pre-commit hooks that will automatically format your code before each commit:

```bash
pre-commit install
```

## API Endpoints

- `GET /health`: Health check endpoint
- `POST /paraphrase`: Rephrase text using the OpenRouter API
- `POST /rephrase`: Rephrase text for Slack integration
- `GET /signin-oidc`: Handle Slack OAuth callback

## Project Structure

```
slackparaphrase/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── paraphrase.py
│   │   ├── slack.py
│   │   └── openrouter.py
│   └── services/
│       ├── __init__.py
│       └── paraphrase.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── .pre-commit-config.yaml
└── .env
```

## License

MIT

