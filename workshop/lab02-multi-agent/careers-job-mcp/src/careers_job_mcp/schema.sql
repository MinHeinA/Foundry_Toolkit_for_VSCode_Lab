PRAGMA page_size = 4096;
PRAGMA auto_vacuum = NONE;
PRAGMA encoding = 'UTF-8';

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE jobs (
    job_key TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL,
    job_id TEXT NOT NULL,
    posting_no TEXT NOT NULL,
    title TEXT NOT NULL,
    agency TEXT NOT NULL,
    agency_description TEXT NOT NULL,
    start_date_ms INTEGER NOT NULL,
    closing_date_ms INTEGER,
    employment_type TEXT NOT NULL,
    work_arrangement TEXT NOT NULL,
    experience_required TEXT NOT NULL,
    experience_years_min INTEGER NOT NULL,
    experience_years_max INTEGER NOT NULL,
    field TEXT NOT NULL,
    functional_area TEXT NOT NULL,
    industry TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    responsibilities TEXT NOT NULL,
    requirements TEXT NOT NULL,
    source_url TEXT NOT NULL,
    PRIMARY KEY (job_key)
);

CREATE INDEX jobs_agency_idx ON jobs(agency COLLATE NOCASE);
CREATE INDEX jobs_field_idx ON jobs(field COLLATE NOCASE);
CREATE INDEX jobs_employment_type_idx ON jobs(employment_type COLLATE NOCASE);
CREATE INDEX jobs_experience_min_idx ON jobs(experience_years_min);

CREATE VIRTUAL TABLE jobs_fts USING fts5(
    title,
    agency,
    field,
    industry,
    description,
    responsibilities,
    requirements,
    content = 'jobs',
    content_rowid = 'rowid',
    tokenize = 'unicode61 remove_diacritics 2'
);
