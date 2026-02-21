-- Stage 9 expansion: additional startup strategy sources.

INSERT INTO sources (name, domain, start_urls, allowed_paths, blocked_paths, max_depth, max_pages, is_active, metadata)
VALUES
(
    'sequoia_arc',
    'arc.sequoiacap.com',
    '["https://arc.sequoiacap.com/"]'::jsonb,
    '["/"]'::jsonb,
    '[]'::jsonb,
    2,
    180,
    TRUE,
    '{"topic":"ops","type":"frameworks"}'::jsonb
),
(
    'stripe_atlas_guides',
    'stripe.com',
    '["https://stripe.com/atlas/guides"]'::jsonb,
    '["/atlas/guides","/atlas"]'::jsonb,
    '["/pricing"]'::jsonb,
    2,
    140,
    TRUE,
    '{"topic":"fundraising","type":"company_formation"}'::jsonb
),
(
    'reforge_blog',
    'www.reforge.com',
    '["https://www.reforge.com/blog"]'::jsonb,
    '["/blog"]'::jsonb,
    '[]'::jsonb,
    2,
    120,
    TRUE,
    '{"topic":"growth","type":"growth_strategy"}'::jsonb
),
(
    'lenny_newsletter_public',
    'www.lennysnewsletter.com',
    '["https://www.lennysnewsletter.com/"]'::jsonb,
    '["/p/"]'::jsonb,
    '["/api"]'::jsonb,
    1,
    120,
    TRUE,
    '{"topic":"product","type":"product_growth"}'::jsonb
),
(
    'saastr_blog',
    'www.saastr.com',
    '["https://www.saastr.com/blog/"]'::jsonb,
    '["/blog"]'::jsonb,
    '[]'::jsonb,
    2,
    180,
    TRUE,
    '{"topic":"go_to_market","type":"saas_scaling"}'::jsonb
)
ON CONFLICT (name)
DO UPDATE SET
    domain = EXCLUDED.domain,
    start_urls = EXCLUDED.start_urls,
    allowed_paths = EXCLUDED.allowed_paths,
    blocked_paths = EXCLUDED.blocked_paths,
    max_depth = EXCLUDED.max_depth,
    max_pages = EXCLUDED.max_pages,
    is_active = EXCLUDED.is_active,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();
