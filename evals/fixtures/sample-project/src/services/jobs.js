const { db } = require('../db');
const { enqueue } = require('../queue');

const MAX_ATTEMPTS = 3;

function createJob(task, payload) {
  const id = `job_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
  db.prepare('INSERT INTO jobs (id, task, payload, status, attempts) VALUES (?, ?, ?, ?, 0)').run(
    id,
    task,
    JSON.stringify(payload),
    'pending'
  );
  enqueue(id);
  return { id, status: 'pending' };
}

function getJob(id) {
  return db.prepare('SELECT id, task, status, attempts, result FROM jobs WHERE id = ?').get(id);
}

function markRunning(id) {
  db.prepare("UPDATE jobs SET status = 'running', attempts = attempts + 1 WHERE id = ?").run(id);
}

function markDone(id, result) {
  db.prepare("UPDATE jobs SET status = 'done', result = ? WHERE id = ?").run(
    JSON.stringify(result),
    id
  );
}

// `permanent` is for failures retrying cannot fix — an unknown task name stays
// unknown, so retrying it just spins the worker until the process dies.
function markFailed(id, { permanent = false } = {}) {
  const job = getJob(id);
  const status = permanent || job.attempts >= MAX_ATTEMPTS ? 'failed' : 'pending';
  db.prepare('UPDATE jobs SET status = ? WHERE id = ?').run(status, id);
  if (status === 'pending') enqueue(id);
  return status;
}

module.exports = { createJob, getJob, markRunning, markDone, markFailed, MAX_ATTEMPTS };
