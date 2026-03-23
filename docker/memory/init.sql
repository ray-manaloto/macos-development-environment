-- docker/memory/init.sql
-- PostgreSQL init script for Honcho.
-- Enables the pgvector extension required for vector similarity search.
-- This runs once when the database is first created.
CREATE EXTENSION IF NOT EXISTS vector;
