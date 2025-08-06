-- PostgreSQL initialization script
-- Creates extensions and initial setup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSON extensions
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create user if not exists (handled by Docker environment variables)
-- This file is mainly for additional setup

-- Set default timezone
SET timezone = 'UTC';

-- Log successful initialization
INSERT INTO information_schema.sql_languages (sql_language_source) 
SELECT 'AI Video Generator PostgreSQL initialization completed at ' || NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.sql_languages 
    WHERE sql_language_source LIKE 'AI Video Generator%'
);