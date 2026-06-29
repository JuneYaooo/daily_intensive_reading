# Daily Intensive Reading Frontend

React/Vite frontend for the Daily Intensive Reading curation tool.

## Setup

Install dependencies:

```bash
npm install
```

Optional API configuration for local development:

```bash
cp .env.example .env.local
```

`VITE_API_URL` may be either an API root such as `http://localhost:5000/api` or an origin such as `http://localhost:5000`. The frontend service layer calls `/api/...` paths and normalizes a trailing `/api` automatically.

## Scripts

```bash
npm run dev      # start Vite dev server on port 5300
npm run build    # production build
npm run lint     # ESLint
npm run preview  # preview production build
```

For the full Docker stack, run from the repository root:

```bash
docker compose up --build
```

## Development URLs

- Vite dev server: `http://localhost:5300`
- Docker reverse proxy: `http://localhost:20001`

In dev mode, Vite proxies `/api` to `http://localhost:20001`.

## Backend API Used By The Frontend

- `GET /api/sources/`
- `POST /api/sources/`
- `PUT /api/sources/{id}`
- `DELETE /api/sources/{id}`
- `GET /api/prompts/`
- `GET /api/prompts/defaults/{type}`
- `POST /api/prompts/`
- `PUT /api/prompts/{id}`
- `DELETE /api/prompts/{id}`
- `GET /api/cards/`
- `POST /api/cards/create`
- `PUT /api/cards/{id}`
- `DELETE /api/cards/{id}`
- `POST /api/daily-reading/generate`
- `POST /api/daily-reading/generate-one-card`
- `POST /api/daily-reading/generate-poster`
