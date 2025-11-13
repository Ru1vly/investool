-- ============================================================================
-- PostgreSQL Initialization Script for FinRisk AI
--
-- Creates database schema and enables required extensions.
-- Executed automatically when PostgreSQL container starts for the first time.
-- ============================================================================

-- Enable pgvector extension for vector embeddings (RAG)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Mem0 User Memory Tables
-- ============================================================================

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id VARCHAR(255) PRIMARY KEY,
    risk_tolerance VARCHAR(50) NOT NULL DEFAULT 'moderate',
    reporting_style VARCHAR(50) NOT NULL DEFAULT 'detailed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User activity history
CREATE TABLE IF NOT EXISTS user_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    activity_type VARCHAR(100) NOT NULL,
    content JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_preferences(user_id) ON DELETE CASCADE
);

-- Create index on user_id and timestamp for efficient queries
CREATE INDEX IF NOT EXISTS idx_user_activities_user_id
    ON user_activities(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_user_activities_session_id
    ON user_activities(session_id);

-- ============================================================================
-- RAG Vector Storage Tables
-- ============================================================================

-- Document embeddings for vector search
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    embedding vector(384),  -- sentence-transformers/all-MiniLM-L6-v2 dimension
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create HNSW index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector
    ON document_embeddings
    USING hnsw (embedding vector_cosine_ops);

-- Metadata index for filtering
CREATE INDEX IF NOT EXISTS idx_document_embeddings_metadata
    ON document_embeddings USING GIN (metadata);

-- ============================================================================
-- Report Cache Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS report_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    user_query TEXT NOT NULL,
    final_report_text TEXT NOT NULL,
    calculation_results JSONB NOT NULL,
    chart_json JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_preferences(user_id) ON DELETE CASCADE
);

-- Create index for user report retrieval
CREATE INDEX IF NOT EXISTS idx_report_cache_user_id
    ON report_cache(user_id, created_at DESC);

-- ============================================================================
-- Temporal Insights Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS temporal_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    insight_text TEXT NOT NULL,
    confidence_score FLOAT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_preferences(user_id) ON DELETE CASCADE
);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for user_preferences
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Insert sample user for testing
INSERT INTO user_preferences (user_id, risk_tolerance, reporting_style)
VALUES ('test_user_123', 'moderate', 'detailed')
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify extensions
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('vector', 'uuid-ossp');

-- Verify tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- ============================================================================
-- Grants (if using separate application user)
-- ============================================================================

-- Grant all privileges to the application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finrisk_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finrisk_user;

-- ============================================================================
-- Database initialized successfully!
-- ============================================================================
