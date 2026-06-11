# Database configuration
import os

# Neon DB (PostgreSQL) Connections

# Use the pooled connection for the Streamlit dashboard to manage many concurrent read connections.
DB_URI_POOLED = "postgresql://neondb_owner:npg_Mo9aWekEitx5@ep-shiny-lake-aou4p5lj-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Use the non-pooled connection for backend ETL and long-running scripts to prevent pool exhaustion.
DB_URI_NON_POOLED = "postgresql://neondb_owner:npg_Mo9aWekEitx5@ep-shiny-lake-aou4p5lj.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# For SQLAlchemy, we need to prefix the protocol if it uses psycopg2 explicitly:
# "postgresql+psycopg2://..."
# However, SQLAlchemy automatically picks up psycopg2 when using "postgresql://"

DB_URI_POOLED_SA = DB_URI_POOLED.replace("postgresql://", "postgresql+psycopg2://")
DB_URI_NON_POOLED_SA = DB_URI_NON_POOLED.replace("postgresql://", "postgresql+psycopg2://")
