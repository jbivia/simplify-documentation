const { db } = require('./index');

db.exec(`
  CREATE TABLE IF NOT EXISTS jobs (
    id       TEXT PRIMARY KEY,
    task     TEXT NOT NULL,
    payload  TEXT NOT NULL,
    status   TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    result   TEXT
  );
  CREATE INDEX IF NOT EXISTS jobs_status ON jobs (status);
`);

console.log('migrations applied');
