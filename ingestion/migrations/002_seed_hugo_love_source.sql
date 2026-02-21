-- Stage 2 seed: first crawl source (hugo.love)

INSERT INTO sources (
    name,
    domain,
    start_urls,
    allowed_paths,
    blocked_paths,
    max_depth,
    max_pages,
    is_active,
    metadata
)
VALUES (
    'hugo_love',
    'hugo.love',
    '["https://hugo.love/"]'::jsonb,
    '["/","/about","/blog","/products","/pricing","/features"]'::jsonb,
    '["/cdn-cgi","/wp-admin","/wp-login","/cart","/checkout","/privacy","/terms"]'::jsonb,
    3,
    400,
    TRUE,
    '{"topic":"startup_case_study","notes":"Initial source for startup strategy corpus."}'::jsonb
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
