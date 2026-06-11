# Database configuration
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neon DB (PostgreSQL) Connections

# Use the pooled connection for the Streamlit dashboard to manage many concurrent read connections.
DB_URI_POOLED = os.getenv("DB_URI_POOLED", "")

# Use the non-pooled connection for backend ETL and long-running scripts to prevent pool exhaustion.
DB_URI_NON_POOLED = os.getenv("DB_URI_NON_POOLED", "")

# For SQLAlchemy, we need to prefix the protocol if it uses psycopg2 explicitly:
# "postgresql+psycopg2://..."
# However, SQLAlchemy automatically picks up psycopg2 when using "postgresql://"

DB_URI_POOLED_SA = DB_URI_POOLED.replace("postgresql://", "postgresql+psycopg2://") if DB_URI_POOLED else ""
DB_URI_NON_POOLED_SA = DB_URI_NON_POOLED.replace("postgresql://", "postgresql+psycopg2://") if DB_URI_NON_POOLED else ""
