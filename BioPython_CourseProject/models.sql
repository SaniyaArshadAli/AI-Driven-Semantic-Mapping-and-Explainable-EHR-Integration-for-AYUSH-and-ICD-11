CREATE TABLE IF NOT EXISTS semantic_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ayush_term TEXT,
    ayush_description TEXT,
    icd11_term TEXT,
    confidence REAL,
    reason TEXT,
    status TEXT DEFAULT 'PENDING',
    reviewed_by TEXT,
    reviewed_at TEXT
);
