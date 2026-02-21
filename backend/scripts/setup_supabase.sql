-- Run this in the Supabase SQL editor to set up the required schema.

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table for embeddings
CREATE TABLE IF NOT EXISTS documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company     TEXT NOT NULL,
    source_type TEXT NOT NULL,        -- 'patent' | 'news' | 'product_image'
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    image_url   TEXT,
    embedding   vector(768),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Cosine similarity index (IVFFlat)
CREATE INDEX IF NOT EXISTS documents_embedding_idx
    ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for company + source_type filtering
CREATE INDEX IF NOT EXISTS documents_company_type_idx
    ON documents (company, source_type);

-- Similarity search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(768),
    filter_company  text,
    filter_types    text[],
    match_count     int
)
RETURNS TABLE (
    id          uuid,
    company     text,
    source_type text,
    content     text,
    metadata    jsonb,
    image_url   text,
    similarity  float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.company,
        d.source_type,
        d.content,
        d.metadata,
        d.image_url,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE d.company = filter_company
      AND (filter_types IS NULL OR d.source_type = ANY(filter_types))
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Enable RLS (use service role key from backend to bypass)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: allow service role full access (backend uses service key)
CREATE POLICY "service_role_all" ON documents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
