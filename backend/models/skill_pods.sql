-- Skill enrollments table
CREATE TABLE IF NOT EXISTS skill_enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    path_id TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    completed_skills TEXT,  -- JSON array of completed skill IDs
    assessment_results TEXT,  -- JSON object with assessment scores
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);