from config.db import Base, engine
from models.models import Source, Prompt, FavoriteCard

def initialize_database():
    """
    Create all necessary tables in the database if they don't exist.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    initialize_database() 