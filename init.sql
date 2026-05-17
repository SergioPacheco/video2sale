-- Affiliate Video Factory — Schema v2
-- Opção B: normalizado com rastreabilidade, aprovação humana, Amazon PA-API + CSV

-- ============================================================
-- PRODUTOS
-- ============================================================

-- Buscas/importações de produtos (Amazon PA-API ou CSV manual)
CREATE TABLE IF NOT EXISTS product_searches (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'manual_csv',  -- 'amazon_pa_api', 'tiktok_shop', 'manual_csv'
    keywords TEXT,
    category TEXT,
    marketplace TEXT DEFAULT 'amazon.es',       -- 'amazon.es', 'tiktok_shop_es'
    results_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Produtos candidatos
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    search_id INT REFERENCES product_searches(id),
    -- Identificação
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT DEFAULT 'TikTok Shop',
    asin TEXT,                                  -- ID Amazon (se veio da PA-API)
    -- URLs
    product_url TEXT,
    shop_url TEXT,
    affiliate_url TEXT,                         -- link de afiliado gerado
    image_url TEXT,                             -- imagem principal do produto
    -- Dados do marketplace
    price NUMERIC(10,2),
    currency TEXT DEFAULT 'EUR',
    rating NUMERIC(3,2),                        -- avaliação (ex: 4.5)
    reviews_count INT DEFAULT 0,
    -- Scores (preenchidos por humano ou LLM)
    pain_score INT DEFAULT 0,
    visual_score INT DEFAULT 0,
    trend_score INT DEFAULT 0,
    competition_score INT DEFAULT 0,
    availability_score INT DEFAULT 0,
    demo_score INT DEFAULT 0,
    impulse_buy_score INT DEFAULT 0,
    commission_estimate NUMERIC(5,2) DEFAULT 0,
    -- Calculado
    total_score NUMERIC(5,2) DEFAULT 0,
    -- Meta
    notes TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_asin ON products(asin);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_score ON products(total_score DESC);

-- ============================================================
-- VÍDEOS
-- ============================================================

-- Vencedores semanais
CREATE TABLE IF NOT EXISTS weekly_winners (
    id SERIAL PRIMARY KEY,
    week TEXT NOT NULL,                         -- '2026-W21'
    product_id INT REFERENCES products(id),
    score NUMERIC(5,2),
    reason TEXT,
    approved_by TEXT DEFAULT 'system',          -- 'system' ou 'human'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weekly_winners_week ON weekly_winners(week);

-- Registro principal do vídeo
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    week TEXT NOT NULL,
    template TEXT,                              -- 'problema-solucao', 'antes-depois', etc.
    -- Referência ao creative pack selecionado
    selected_creative_pack_id INT,             -- FK adicionada após criar tabela
    -- Arquivos gerados
    voiceover_path TEXT,
    video_path TEXT,
    thumbnail_path TEXT,
    -- Renderer
    renderer TEXT DEFAULT 'seedance',
    renderer_config JSONB,
    -- Prompt templates usados (rastreabilidade)
    script_prompt_id INT REFERENCES prompt_templates(id),
    renderer_prompt_id INT REFERENCES prompt_templates(id),
    -- Estado
    status TEXT DEFAULT 'pending_creative',
    -- Custo real acumulado
    total_cost NUMERIC(8,4) DEFAULT 0,
    -- Meta
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_videos_week ON videos(week);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_product ON videos(product_id);

-- ============================================================
-- PACOTES CRIATIVOS (versões do roteiro)
-- ============================================================

CREATE TABLE IF NOT EXISTS video_creative_packs (
    id SERIAL PRIMARY KEY,
    video_id INT REFERENCES videos(id) ON DELETE CASCADE,
    version INT DEFAULT 1,                     -- 1, 2, 3 (múltiplas variações)
    -- Conteúdo criativo
    hook TEXT,                                  -- gancho (primeiros 2s)
    script_json JSONB,                         -- cenas completas [{start, end, text, voiceover, visual}]
    caption TEXT,                               -- legenda para redes sociais
    hashtags TEXT[],                            -- array de hashtags
    affiliate_disclaimer TEXT,
    -- Compliance
    compliance_status TEXT DEFAULT 'pending',   -- 'pending', 'approved', 'adjusted', 'rejected'
    compliance_notes TEXT,
    -- Seleção humana
    selected BOOLEAN DEFAULT FALSE,
    -- Meta
    model_used TEXT,                            -- 'gpt-4.1-mini'
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    cost NUMERIC(8,6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_creative_packs_video ON video_creative_packs(video_id);

-- FK de videos → creative_packs (após criação da tabela)
ALTER TABLE videos
    ADD CONSTRAINT fk_selected_creative_pack
    FOREIGN KEY (selected_creative_pack_id)
    REFERENCES video_creative_packs(id);

-- ============================================================
-- EVENTOS (log de rastreabilidade)
-- ============================================================

CREATE TABLE IF NOT EXISTS video_events (
    id SERIAL PRIMARY KEY,
    video_id INT REFERENCES videos(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    -- Tipos: product_ranked, creative_generated, compliance_checked,
    --        human_selected_pack, tts_generated, video_rendered,
    --        human_approved, human_rejected, published, error
    actor TEXT DEFAULT 'system',               -- 'system' ou 'human'
    details JSONB,                             -- metadados livres (custo, modelo, erro, etc.)
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_video ON video_events(video_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON video_events(event_type);

-- ============================================================
-- PROMPT TEMPLATES
-- ============================================================

CREATE TABLE IF NOT EXISTS prompt_templates (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,                         -- 'script_agent', 'compliance', 'seedance_prompt', 'runway_prompt', 'tts_instructions'
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    variables TEXT[] DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_type ON prompt_templates(type);

-- ============================================================
-- ESTADOS POSSÍVEIS (referência)
-- ============================================================
-- videos.status:
--   pending_creative    → aguardando geração de roteiro
--   creative_generated  → roteiro(s) gerado(s), aguardando compliance
--   compliance_done     → compliance verificou, aguardando seleção humana
--   human_selected      → humano escolheu roteiro, aguardando TTS
--   tts_generated       → áudio gerado, aguardando render
--   rendering           → renderizando vídeo
--   rendered            → vídeo pronto, aguardando aprovação humana
--   approved            → humano aprovou, pronto para publicar
--   rejected            → humano rejeitou
--   published           → publicado manualmente
--   error               → erro em alguma etapa

-- ============================================================
-- SEED: PROMPT TEMPLATES PADRÃO
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
