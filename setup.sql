-- Group 7 Neon PostgreSQL experiment setup
CREATE TABLE IF NOT EXISTS group7_benchmark (
    id BIGSERIAL PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO group7_benchmark (payload)
SELECT 'Group 7 sample record ' || g
FROM generate_series(1, 5000) AS g
WHERE NOT EXISTS (SELECT 1 FROM group7_benchmark LIMIT 1);

CREATE INDEX IF NOT EXISTS idx_group7_benchmark_created_at
ON group7_benchmark(created_at);
