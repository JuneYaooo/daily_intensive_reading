# Daily Intensive Reading

A React application for managing daily intensive reading cards.

## Setup

1. Install dependencies:
   ```
   npm install
   ```

2. Set up MySQL database:
   - Create a database schema
   - Use the provided SQL script in `server/database.sql`
   - Configure database connection in `.env.local` file:

   ```
   VITE_API_URL=http://0.0.0.0:5300/api
   
   VITE_MYSQL_HOST=localhost
   VITE_MYSQL_PORT=3399
   VITE_MYSQL_USER=root
   VITE_MYSQL_PASSWORD=literature
   VITE_MYSQL_DATABASE=everyday_card
   ```

3. Run the application:
   - For development with both frontend and backend:
     ```
     npm run dev:all
     ```
   - For frontend only:
     ```
     npm run dev
     ```
   - For backend only:
     ```
     npm run server
     ```

4. Access the application:
   - Frontend: `http://[your-ip-address]:5300`
   - Backend API: `http://[your-ip-address]:5300/api`

## Database Schema

### Tables

1. **reading_cards**: Stores the main reading content
   - id (INT, primary key)
   - title (VARCHAR)
   - content (TEXT)
   - author (VARCHAR, optional)
   - source (VARCHAR, optional)
   - tags (VARCHAR, optional)
   - created_at (TIMESTAMP)
   - updated_at (TIMESTAMP)

2. **tags**: Stores tag names
   - id (INT, primary key)
   - name (VARCHAR, unique)
   - created_at (TIMESTAMP)

3. **card_tags**: Junction table for many-to-many card-tag relationship
   - card_id (INT, foreign key)
   - tag_id (INT, foreign key)

4. **user_interactions**: Tracks user engagement with cards
   - id (INT, primary key)
   - user_id (INT)
   - card_id (INT, foreign key)
   - interaction_type (ENUM: 'read', 'favorite', 'comment')
   - comment (TEXT, optional)
   - created_at (TIMESTAMP)

## API Endpoints

- `GET /api/cards` - Get all cards with pagination
- `GET /api/cards/:id` - Get a single card by ID
- `POST /api/cards` - Create a new card
- `PUT /api/cards/:id` - Update an existing card
- `DELETE /api/cards/:id` - Delete a card
- `GET /api/cards/search?q=query` - Search cards by query
