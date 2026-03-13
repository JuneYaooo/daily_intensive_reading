# Daily Intensive Reading Backend

每日精读后端 (Daily Intensive Reading Backend)

## Features

This backend provides APIs for:

1. Information source management (add, modify, delete)
2. Prompt preset management
3. Report generation (using OpenAI models)
4. Card management (generate, save, unsave, view saved cards)
5. Generate cards from selected specific content
6. Daily intensive reading generation with JigsawStack (primary) and Firecrawl (fallback) crawlers, integrated with DeepSeek

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file with your database credentials, OpenAI API key, DeepSeek API key, JigsawStack API keys, and Firecrawl API token.

3. Initialize the database:
use Alembic

4. Start the server:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app.app:app
```

## Database Migrations with Alembic

This project uses Alembic for database migrations. Here's how to use it:

1. Generate a new migration:
```bash
python -m app.migrations_helper generate "init migration"
```

2. Apply migrations to update the database:
```bash
python -m app.migrations_helper upgrade
```

3. Rollback migrations:
```bash
python -m app.migrations_helper downgrade
```

4. View migration history:
```bash
alembic history
```

5. View current database revision:
```bash
alembic current
```

## API Documentation

### Sources API

- `GET /api/sources/` - Get all sources
- `GET /api/sources/{id}` - Get a specific source
- `POST /api/sources/` - Create a new source
- `PUT /api/sources/{id}` - Update a source
- `DELETE /api/sources/{id}` - Delete a source

### Prompts API

- `GET /api/prompts/` - Get all prompts
- `GET /api/prompts/{id}` - Get a specific prompt
- `POST /api/prompts/` - Create a new prompt
- `PUT /api/prompts/{id}` - Update a prompt
- `DELETE /api/prompts/{id}` - Delete a prompt

### Reports API

- `POST /api/reports/generate` - Generate a report from content using a prompt

### Cards API

- `GET /api/cards/` - Get all cards
- `GET /api/cards/{id}` - Get a specific card
- `POST /api/cards/generate` - Generate a card from selected content
- `POST /api/cards/favorite` - Favorite a card
- `POST /api/cards/unfavorite` - Unfavorite a card
- `GET /api/cards/favorites/{user_id}` - Get all favorites for a user

### Daily Reading API

- `POST /api/daily-reading/generate` - Generate daily intensive reading content
  - Uses Firecrawl to batch scrape content
  - Filters and ranks URLs using DeepSeek
  - Generates summary cards for top content
- `GET /api/daily-reading/history` - Get history of previously generated readings
- `GET /api/daily-reading/history/{filename}` - Get details of a specific reading

## Database Schema

The system uses the following main tables:

- `sources`: Information sources
- `prompts`: Prompt presets for report/card generation
- `reading_cards`: Generated cards and reports
- `tags`: Card categorization 
- `card_tags`: Junction table for cards and tags
- `user_interactions`: User actions with cards (favorites, etc.)

## Daily Reading Generation Process

The daily reading generation follows this workflow:

1. Batch crawl source URLs using JigsawStack (with Firecrawl fallback)
2. Use DeepSeek with a filter prompt to identify and rank the 10 most relevant URLs
3. Crawl the top 5 URLs to get their full content
4. Generate summary cards for each content using DeepSeek
5. Return the complete results and save them for future reference

## Web Scraping Service

### Overview

The application now uses a hybrid web scraping approach with intelligent fallback:

1. **JigsawStack** (Primary) - AI-powered scraping with smart content extraction
2. **Firecrawl** (Fallback) - Reliable backup scraping service
3. **Redis Cache** - 24-hour content caching to reduce API calls

### Configuration

Add these environment variables to your `.env` file:

```bash
# JigsawStack API Keys (comma-separated for load balancing)
JigsawStack_APIKEYs=sk_key1,sk_key2,sk_key3

# Firecrawl API Token (fallback)
FIRECRAWL_API_TOKEN=fc-your-token-here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### Testing

Run the test script to verify your scraper configuration:

```bash
python test_scraper.py
```

### Features

- **Smart Content Extraction**: JigsawStack uses AI to identify and extract main content
- **Multi-key Support**: Automatically rotates between multiple JigsawStack API keys
- **Intelligent Fallback**: Automatically falls back to Firecrawl if JigsawStack fails
- **Caching**: Redis caching prevents redundant scraping of the same URLs
- **Detailed Logging**: Comprehensive logs for monitoring and debugging

For more details, see [SCRAPER_CONFIG.md](SCRAPER_CONFIG.md).

## Running the Application

```bash
python app/app.py

# Or with uvicorn
uvicorn app.app:app --host 0.0.0.0 --port 5000 --workers 2

# Or with gunicorn
gunicorn -w 2 --timeout 1200 -b 0.0.0.0:5000 wsgi:app
```