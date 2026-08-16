const fs = require('node:fs');
const path = require('node:path');
const Database = require('better-sqlite3');

const DATABASE_URL = process.env.DATABASE_URL || './data/taskrunner.db';

// SQLite will not create the parent directory, and ./data is not in the repo.
fs.mkdirSync(path.dirname(DATABASE_URL), { recursive: true });

const db = new Database(DATABASE_URL);
db.pragma('journal_mode = WAL');

module.exports = { db, DATABASE_URL };
