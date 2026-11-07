CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX idx_sessions_created_at ON sessions(created_at);

CREATE TABLE question_answer_pairs (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question    TEXT NOT NULL,
    raw_answer  TEXT NOT NULL,
    openui_lang TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE INDEX idx_qap_session_created
    ON question_answer_pairs(session_id, created_at);

CREATE TABLE question_answer_relevance (
    pair_id     TEXT PRIMARY KEY
                REFERENCES question_answer_pairs(id) ON DELETE CASCADE,
    relevant    INTEGER NOT NULL DEFAULT 1 CHECK (relevant IN (0, 1)),
    updated_at  TEXT NOT NULL
);

CREATE TABLE reports (
    session_id  TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    openui_lang TEXT NOT NULL,
    incomplete  INTEGER NOT NULL DEFAULT 0 CHECK (incomplete IN (0, 1)),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
