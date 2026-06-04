CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS auth_db;
CREATE SCHEMA IF NOT EXISTS user_db;
CREATE SCHEMA IF NOT EXISTS shop_db;
CREATE SCHEMA IF NOT EXISTS product_db;
CREATE SCHEMA IF NOT EXISTS voucher_db;
CREATE SCHEMA IF NOT EXISTS livestream_db;
CREATE SCHEMA IF NOT EXISTS chat_db;
CREATE SCHEMA IF NOT EXISTS ai_db;
CREATE SCHEMA IF NOT EXISTS order_db;
CREATE SCHEMA IF NOT EXISTS analytics_db;

DO $$ BEGIN CREATE TYPE auth_db.user_role AS ENUM ('CUSTOMER', 'SELLER', 'ADMIN'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE auth_db.account_status AS ENUM ('ACTIVE', 'LOCKED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE livestream_db.livestream_status AS ENUM ('DRAFT', 'LIVE', 'ENDED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE chat_db.sender_type AS ENUM ('CUSTOMER', 'SELLER', 'AI'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE ai_db.ai_response_status AS ENUM ('ANSWERED', 'NEED_SELLER_SUPPORT', 'BLOCKED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS auth_db.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role auth_db.user_role NOT NULL DEFAULT 'CUSTOMER',
    status auth_db.account_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_db.profiles (
    user_id UUID PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    avatar_url TEXT,
    phone VARCHAR(40),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS shop_db.shops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    logo_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_db.products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID NOT NULL,
    name VARCHAR(300) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price NUMERIC(14, 2) NOT NULL CHECK (price >= 0),
    sale_price NUMERIC(14, 2) CHECK (sale_price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    category VARCHAR(100),
    image_url TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    variants JSONB NOT NULL DEFAULT '[]'::jsonb,
    purchase_url TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS voucher_db.vouchers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID NOT NULL,
    code VARCHAR(100) NOT NULL,
    discount_type VARCHAR(30) NOT NULL,
    discount_value NUMERIC(14, 2) NOT NULL CHECK (discount_value >= 0),
    min_order_value NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (min_order_value >= 0),
    start_date DATE,
    end_date DATE,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (shop_id, code)
);

CREATE TABLE IF NOT EXISTS livestream_db.livestreams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status livestream_db.livestream_status NOT NULL DEFAULT 'DRAFT',
    ai_enabled BOOLEAN NOT NULL DEFAULT true,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS livestream_db.livestream_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    livestream_id UUID NOT NULL,
    product_id UUID NOT NULL,
    UNIQUE (livestream_id, product_id)
);

CREATE TABLE IF NOT EXISTS chat_db.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    livestream_id UUID NOT NULL,
    user_id UUID,
    message TEXT NOT NULL,
    sender_type chat_db.sender_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.ai_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    livestream_id UUID NOT NULL,
    customer_message_id UUID,
    ai_message_id UUID,
    confidence_score NUMERIC(4, 3) NOT NULL DEFAULT 0,
    status ai_db.ai_response_status NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.ai_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    livestream_id UUID NOT NULL,
    customer_message_id UUID,
    customer_message TEXT,
    question_type VARCHAR(80),
    retrieved_context JSONB,
    prompt TEXT,
    raw_model_response TEXT,
    final_reply TEXT,
    confidence_score NUMERIC(4, 3) NOT NULL DEFAULT 0,
    status ai_db.ai_response_status NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.knowledge_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID NOT NULL,
    source_type VARCHAR(40) NOT NULL,
    source_id UUID,
    content TEXT NOT NULL,
    embedding vector(1536),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.ai_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID,
    model_name VARCHAR(100) NOT NULL DEFAULT 'llama3.1',
    temperature NUMERIC(3, 2) NOT NULL DEFAULT 0.2,
    max_tokens INTEGER NOT NULL DEFAULT 220,
    reply_style TEXT NOT NULL DEFAULT 'ngắn gọn, thân thiện, chốt đơn',
    auto_reply_enabled BOOLEAN NOT NULL DEFAULT true,
    fallback_to_seller_enabled BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS order_db.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    shop_id UUID NOT NULL,
    total_amount NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS order_db.order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(14, 2) NOT NULL CHECK (price >= 0)
);

CREATE TABLE IF NOT EXISTS analytics_db.livestream_metrics (
    livestream_id UUID PRIMARY KEY,
    viewer_count INTEGER NOT NULL DEFAULT 0,
    question_count INTEGER NOT NULL DEFAULT 0,
    ai_answered_count INTEGER NOT NULL DEFAULT 0,
    ai_failed_count INTEGER NOT NULL DEFAULT 0,
    order_count INTEGER NOT NULL DEFAULT 0,
    revenue NUMERIC(14, 2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS shop_db.sales_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID NOT NULL,
    shipping_fee_note TEXT,
    delivery_time_note TEXT,
    return_policy TEXT,
    warranty_policy TEXT,
    sensitive_scope_note TEXT,
    embedding vector(1536),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (shop_id)
);

CREATE INDEX IF NOT EXISTS idx_product_embeddings
    ON product_db.products USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_ai_knowledge_embeddings
    ON ai_db.knowledge_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chat_messages_livestream_created
    ON chat_db.chat_messages (livestream_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_logs_livestream_created
    ON ai_db.ai_logs (livestream_id, created_at DESC);
