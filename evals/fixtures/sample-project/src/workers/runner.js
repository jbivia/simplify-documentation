const { enqueue, dequeue, size } = require('../queue');
const { markRunning, markDone, markFailed } = require('../services/jobs');
const { db } = require('../db');
const { log } = require('../utils/logger');
const handlers = require('./handlers');

const POLL_MS = Number(process.env.QUEUE_POLL_MS || 500);

// The API runs in its own process, so its in-memory enqueue never reaches us.
// SQLite is the real handoff: pull whatever is still pending on every tick.
function refill() {
  const rows = db.prepare("SELECT id FROM jobs WHERE status = 'pending'").all();
  rows.forEach((row) => enqueue(row.id));
  return rows.length;
}

async function tick() {
  if (size() === 0 && refill() === 0) return;

  const id = dequeue();
  if (!id) return;

  const job = db.prepare('SELECT * FROM jobs WHERE id = ?').get(id);
  const handler = handlers[job.task];
  if (!handler) {
    log('error', `no handler for task ${job.task}`);
    markFailed(id, { permanent: true });
    return;
  }

  markRunning(id);
  try {
    markDone(id, await handler(JSON.parse(job.payload)));
  } catch (err) {
    const status = markFailed(id);
    log('error', `${id} failed (${err.message}) -> ${status}`);
  }
}

log('info', `worker polling every ${POLL_MS}ms`);
setInterval(tick, POLL_MS);
