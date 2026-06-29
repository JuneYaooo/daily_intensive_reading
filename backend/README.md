# Daily Intensive Reading Backend

每日精读后端 (Daily Intensive Reading Backend)

## Features

This backend provides APIs for:

1. Information source management (add, modify, delete)
2. Prompt preset management
3. Report generation (using DeepSeek/OpenAI-compatible models)
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

- `GET /api/cards/` - Get all saved cards
- `GET /api/cards/{id}` - Get a specific card
- `GET /api/cards/search?q=query` - Search saved cards
- `GET /api/cards/popular?limit=10` - Get recent cards
- `GET /api/cards/stats` - Get card statistics
- `POST /api/cards/create` - Create a saved card
- `PUT /api/cards/{id}` - Update a saved card
- `DELETE /api/cards/{id}` - Delete a saved card

### Daily Reading API

- `POST /api/daily-reading/generate` - Generate daily intensive reading content
  - Uses direct HTTP scraping, JigsawStack, and optional Firecrawl fallback
  - Filters and ranks URLs using DeepSeek
  - Generates summary cards for top content
- `GET /api/daily-reading/history` - Get history of previously generated readings
- `GET /api/daily-reading/history/{filename}` - Get details of a specific reading
- `GET /api/daily-reading/quota-status` - Get JigsawStack quota tracking data
- `POST /api/daily-reading/generate-one-card` - Generate one summary card from a URL
- `POST /api/daily-reading/generate-poster` - Generate poster content from a URL

## Database Schema

The system uses the following main tables:

- `sources`: Information sources
- `prompts`: Prompt presets for report/card generation
- `favorite_cards`: Saved summary cards

## Daily Reading Generation Process

The daily reading generation follows this workflow:

1. Batch crawl source URLs using JigsawStack (with Firecrawl fallback)
2. Use DeepSeek with a filter prompt to identify and rank the 10 most relevant URLs
3. Crawl up to the top 5 URLs to get their full content
4. Generate summary cards for each content using DeepSeek
5. Return the complete results and save them for future reference

## Web Scraping Service

### Overview

The application now uses a hybrid web scraping approach with intelligent fallback:

1. **Direct HTTP scraping** - Free first pass for static/SSR pages
2. **JigsawStack** - AI-powered scraping when direct HTTP is insufficient
3. **Firecrawl** - Optional fallback when `FIRECRAWL_API_TOKEN` is configured
4. **Redis Cache** - 14-day content caching to reduce repeated crawling and API calls

### Configuration

Add these environment variables to your `.env` file:

```bash
# JigsawStack API Keys (comma-separated for load balancing)
JigsawStack_APIKEYs=sk_key1,sk_key2,sk_key3

# Firecrawl API Token (fallback)
FIRECRAWL_API_TOKEN=your_firecrawl_api_token_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### Features

- **Smart Content Extraction**: JigsawStack uses AI to identify and extract main content
- **Multi-key Support**: Automatically rotates between multiple JigsawStack API keys
- **Intelligent Fallback**: Falls back from direct HTTP to JigsawStack, and to Firecrawl when configured
- **Caching**: Redis caches successfully scraped URL content for 14 days to prevent redundant scraping
- **Detailed Logging**: Comprehensive logs for monitoring and debugging

## Running the Application

```bash
python -m app.app

# Or with gunicorn
gunicorn -w 2 --timeout 1200 -b 0.0.0.0:5000 wsgi:app
```
