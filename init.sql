-- Video2Sale — Schema v3
-- Ciclo completo: descoberta → material → geração → publicação → métricas

-- ============================================================
-- INTEGRAÇÕES / CONEXÕES DE API
-- ============================================================

CREATE TABLE IF NOT EXISTS integrations (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL UNIQUE,
    api_key TEXT,
    client_id TEXT,
    client_secret TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    status TEXT DEFAULT 'disconnected',
    last_used_at TIMESTAMP,
    last_error TEXT,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- PROMPT TEMPLATES
-- ============================================================

CREATE TABLE IF NOT EXISTS prompt_templates (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    variables TEXT[] DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_type ON prompt_templates(type);

-- ============================================================
-- PRESETS DE GERAÇÃO
-- ============================================================

CREATE TABLE IF NOT EXISTS generation_presets (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    engine TEXT DEFAULT 'ffmpeg',
    template TEXT DEFAULT 'producto_destaque',
    voice TEXT DEFAULT 'nova',
    language TEXT DEFAULT 'es-ES',
    target_duration INT DEFAULT 30,
    music_mode TEXT DEFAULT 'auto',
    variations_count INT DEFAULT 3,
    script_prompt_id INT REFERENCES prompt_templates(id),
    compliance_prompt_id INT REFERENCES prompt_templates(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- PROJETOS / CAMPANHAS
-- ============================================================

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    target_videos INT DEFAULT 5,
    target_platform TEXT DEFAULT 'tiktok',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- PRODUTOS
-- ============================================================

CREATE TABLE IF NOT EXISTS product_searches (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'manual_csv',
    keywords TEXT,
    category TEXT,
    marketplace TEXT DEFAULT 'amazon.es',
    results_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    search_id INT REFERENCES product_searches(id),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT DEFAULT 'TikTok Shop',
    asin TEXT,
    product_url TEXT,
    shop_url TEXT,
    affiliate_url TEXT,
    image_url TEXT,
    price NUMERIC(10,2),
    currency TEXT DEFAULT 'EUR',
    rating NUMERIC(3,2),
    reviews_count INT DEFAULT 0,
    pain_score INT DEFAULT 0,
    visual_score INT DEFAULT 0,
    trend_score INT DEFAULT 0,
    competition_score INT DEFAULT 0,
    availability_score INT DEFAULT 0,
    demo_score INT DEFAULT 0,
    impulse_buy_score INT DEFAULT 0,
    commission_estimate NUMERIC(5,2) DEFAULT 0,
    total_score NUMERIC(5,2) DEFAULT 0,
    notes TEXT,
    description TEXT,
    commission_rate NUMERIC(5,2),
    seller_name TEXT,
    seller_url TEXT,
    accepts_affiliates BOOLEAN DEFAULT FALSE,
    assets JSONB DEFAULT '[]',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_asin ON products(asin);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_score ON products(total_score DESC);

-- ============================================================
-- ASSETS (material centralizado)
-- ============================================================

CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    url TEXT NOT NULL,
    local_path TEXT,
    filename TEXT,
    mime_type TEXT,
    size_bytes INT,
    source TEXT DEFAULT 'manual',
    label TEXT,
    width INT,
    height INT,
    duration_seconds FLOAT,
    used_in_videos INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assets_product ON assets(product_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);

-- ============================================================
-- VÍDEOS
-- ============================================================

CREATE TABLE IF NOT EXISTS weekly_winners (
    id SERIAL PRIMARY KEY,
    week TEXT NOT NULL,
    product_id INT REFERENCES products(id),
    score NUMERIC(5,2),
    reason TEXT,
    approved_by TEXT DEFAULT 'system',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weekly_winners_week ON weekly_winners(week);

CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    project_id INT REFERENCES projects(id),
    preset_id INT REFERENCES generation_presets(id),
    week TEXT NOT NULL,
    template TEXT,
    selected_creative_pack_id INT,
    best_render_id INT,
    voiceover_path TEXT,
    video_path TEXT,
    thumbnail_path TEXT,
    renderer TEXT DEFAULT 'ffmpeg',
    renderer_config JSONB,
    script_prompt_id INT REFERENCES prompt_templates(id),
    renderer_prompt_id INT REFERENCES prompt_templates(id),
    status TEXT DEFAULT 'pending_creative',
    total_cost NUMERIC(8,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_videos_week ON videos(week);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_product ON videos(product_id);
CREATE INDEX IF NOT EXISTS idx_videos_project ON videos(project_id);

-- ============================================================
-- PACOTES CRIATIVOS
-- ============================================================

CREATE TABLE IF NOT EXISTS video_creative_packs (
    id SERIAL PRIMARY KEY,
    video_id INT REFERENCES videos(id) ON DELETE CASCADE,
    version INT DEFAULT 1,
    hook TEXT,
    script_json JSONB,
    caption TEXT,
    hashtags TEXT[],
    affiliate_disclaimer TEXT,
    compliance_status TEXT DEFAULT 'pending',
    compliance_notes TEXT,
    selected BOOLEAN DEFAULT FALSE,
    model_used TEXT,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    cost NUMERIC(8,6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_creative_packs_video ON video_creative_packs(video_id);

ALTER TABLE videos
    ADD CONSTRAINT fk_selected_creative_pack
    FOREIGN KEY (selected_creative_pack_id)
    REFERENCES video_creative_packs(id);

-- ============================================================
-- RENDERS (cada tentativa de renderização)
-- ============================================================

CREATE TABLE IF NOT EXISTS video_renders (
    id SERIAL PRIMARY KEY,
    video_id INT REFERENCES videos(id) ON DELETE CASCADE,
    engine TEXT NOT NULL DEFAULT 'ffmpeg',
    template TEXT,
    voice TEXT DEFAULT 'nova',
    language TEXT DEFAULT 'es-ES',
    target_duration INT DEFAULT 30,
    music_track TEXT,
    video_path TEXT,
    thumbnail_path TEXT,
    duration_seconds FLOAT,
    resolution TEXT DEFAULT '1080x1920',
    file_size_bytes INT,
    llm_cost NUMERIC(8,6) DEFAULT 0,
    tts_cost NUMERIC(8,6) DEFAULT 0,
    render_cost NUMERIC(8,6) DEFAULT 0,
    total_cost NUMERIC(8,4) DEFAULT 0,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_renders_video ON video_renders(video_id);
CREATE INDEX IF NOT EXISTS idx_renders_status ON video_renders(status);

ALTER TABLE videos
    ADD CONSTRAINT fk_best_render
    FOREIGN KEY (best_render_id)
    REFERENCES video_renders(id);

-- ============================================================
-- EVENTOS
-- ============================================================

CREATE TABLE IF NOT EXISTS video_events (
    id SERIAL PRIMARY KEY,
    video_id INT REFERENCES videos(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    actor TEXT DEFAULT 'system',
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_video ON video_events(video_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON video_events(event_type);

-- ============================================================
-- PUBLICAÇÕES
-- ============================================================

CREATE TABLE IF NOT EXISTS publications (
    id SERIAL PRIMARY KEY,
    video_id INT REFERENCES videos(id),
    render_id INT REFERENCES video_renders(id),
    platform TEXT NOT NULL,
    account_name TEXT,
    external_id TEXT,
    external_url TEXT,
    caption_used TEXT,
    hashtags_used TEXT[],
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    saves INT DEFAULT 0,
    status TEXT DEFAULT 'draft',
    error_message TEXT,
    metrics_updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_publications_video ON publications(video_id);
CREATE INDEX IF NOT EXISTS idx_publications_platform ON publications(platform);

-- ============================================================
-- SEED: PROMPT TEMPLATES
-- ============================================================

INSERT INTO prompt_templates (type, name, content, variables) VALUES
('script_agent', 'TikTok Shop — Estándar', E'Eres un estratega de vídeos cortos para TikTok Shop y afiliados.\n\nCrea un paquete creativo para un vídeo vertical de 30 segundos.\n\nProducto: {{product_name}}\nCategoría: {{category}}\nPúblico: {{audience}}\nDolor principal: {{pain}}\nBeneficios permitidos: {{allowed_claims}}\nRestricciones: {{restrictions}}\nIdioma: Español de España.\n\nReglas:\n- Gancho en los primeros 2 segundos.\n- Tono vendedor, rápido, natural y popular.\n- No inventar características.\n- No prometer resultados imposibles.\n- No citar precio fijo.\n- No usar alegaciones médicas.\n- No usar \"garantizado\", \"milagroso\", \"el mejor\".\n- Incluir CTA para link del producto / TikTok Shop.\n- Incluir aviso de afiliado.\n- Dividir en escenas de 2 a 5 segundos.\n- Generar texto en pantalla para cada escena.\n- Generar narración corta para cada escena.\n- Generar descripción visual de cada escena.\n- Generar caption para TikTok, Instagram y Shorts.\n\nDevuelve JSON válido con esta estructura:\n{\n  \"hook\": \"...\",\n  \"script\": \"...\",\n  \"scenes\": [\n    {\"start\": 0, \"end\": 3, \"text\": \"...\", \"voiceover\": \"...\", \"visual\": \"...\"}\n  ],\n  \"caption\": \"...\",\n  \"hashtags\": [],\n  \"affiliate_disclaimer\": \"...\"\n}',
 ARRAY['product_name', 'category', 'audience', 'pain', 'allowed_claims', 'restrictions']),

('compliance', 'Compliance — Estándar', E'Revisa el paquete creativo a continuación para contenido de afiliados y TikTok Shop.\n\nVerifica:\n1. Promesas exageradas.\n2. Beneficios inventados.\n3. Alegaciones médicas o financieras.\n4. Precio fijo que puede cambiar.\n5. Falta de aviso de afiliado.\n6. CTA engañoso.\n7. Uso indebido de marca.\n\nSi hay problemas, corrige manteniendo el estilo vendedor.\n\nDevuelve JSON:\n{\n  \"status\": \"APROBADO|AJUSTAR|REPROBADO\",\n  \"problems\": [],\n  \"fixed_creative_pack\": {}\n}',
 ARRAY[]::TEXT[]),

('seedance_prompt', 'Seedance — Producto Estándar', E'{{visual}}. Vertical 9:16, realistic product video, {{category}}, clean background, natural lighting, TikTok style, smooth camera movement, high quality product demonstration.',
 ARRAY['visual', 'product_name', 'category']),

('runway_prompt', 'Runway — Cinemático', E'{{visual}}. Cinematic vertical shot, product demonstration, smooth camera movement, 4K quality, professional lighting, shallow depth of field, {{category}} product showcase.',
 ARRAY['visual', 'product_name', 'category']),

('tts_instructions', 'Voz — Energética España', E'Habla con energía y entusiasmo natural. Tono de influencer español joven (25-35 años). Ritmo rápido pero claro. Énfasis en las palabras clave del producto. Pausa breve antes del CTA final.',
 ARRAY[]::TEXT[])
ON CONFLICT DO NOTHING;

-- ============================================================
-- SEED: PRESET PADRÃO
-- ============================================================

INSERT INTO generation_presets (name, is_default, engine, template, voice, language, target_duration, music_mode, variations_count)
VALUES ('Estándar TikTok', TRUE, 'ffmpeg', 'producto_destaque', 'nova', 'es-ES', 30, 'auto', 3)
ON CONFLICT DO NOTHING;

-- ============================================================
-- SEED: INTEGRAÇÕES
-- ============================================================

INSERT INTO integrations (provider, status) VALUES
('openai', 'disconnected'),
('tiktok', 'disconnected'),
('amazon', 'disconnected'),
('serper', 'disconnected'),
('runway', 'disconnected'),
('kling', 'disconnected')
ON CONFLICT DO NOTHING;
