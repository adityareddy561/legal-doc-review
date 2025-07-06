import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy import text


# Load environment variables from .env file
load_dotenv()

# Get the Postgres connection string from environment variables
postgres_connection = os.getenv("POSTGRES_CONNECTION")

# Check if the connection string is set
if not postgres_connection:
    raise ValueError("POSTGRES_CONNECTION environment variable is not set.")

# Create the SQLAlchemy engine
engine = create_engine(postgres_connection)


def init_db():
    with engine.connect() as connection:
        # Create the pgvector extension if it doesn't exist
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Create the documents table if it doesn't exist
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS legal_chunks (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                document_id TEXT,
                chunk_text TEXT,
                embedding vector(1536) NOT NULL
            );
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_document_user ON legal_chunks (user_id, document_id);
        """))

        connection.commit()
        print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
    print("Database connection established and initialized.")