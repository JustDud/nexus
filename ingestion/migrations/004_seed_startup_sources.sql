-- Stage 9: multi-source startup catalog seed.

INSERT INTO sources (
    name, domain, start_urls, allowed_paths, blocked_paths,
    max_depth, max_pages, is_active, metadata
)
VALUES
(
    'hugo_love',
    'hugo.love',
    '["https://hugo.love/"]'::jsonb,
    '["/","/about","/blog","/products","/pricing","/features"]'::jsonb,
    '["/cdn-cgi","/wp-admin","/wp-login","/cart","/checkout","/privacy","/terms"]'::jsonb,
    3,
    400,
    FALSE,
    '{"topic":"startup_case_study","notes":"May be robots-restricted. Keep disabled by default."}'::jsonb
),
(
    'paul_graham_essays',
    'paulgraham.com',
    '["https://paulgraham.com/articles.html"]'::jsonb,
    '["/"]'::jsonb,
    '[]'::jsonb,
    2,
    200,
    TRUE,
    '{"topic":"startup_strategy","type":"essays"}'::jsonb
),
(
    'ycombinator_library',
    'www.ycombinator.com',
    '["https://www.ycombinator.com/library"]'::jsonb,
    '["/library"]'::jsonb,
    '["/apply","/companies","/jobs"]'::jsonb,
    2,
    200,
    TRUE,
    '{"topic":"startup_strategy","type":"playbooks"}'::jsonb
),
(
    'a16z_speedrun',
    'speedrun.a16z.com',
    '["https://speedrun.a16z.com/"]'::jsonb,
    '["/"]'::jsonb,
    '[]'::jsonb,
    2,
    180,
    TRUE,
    '{"topic":"technical_startups","type":"accelerator_content"}'::jsonb
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
