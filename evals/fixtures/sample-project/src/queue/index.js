// In-process FIFO buffer. Not the source of truth — the jobs table is. The
// worker refills this from SQLite each tick, so a restart loses nothing.
const pending = [];

function enqueue(jobId) {
  if (!pending.includes(jobId)) pending.push(jobId);
}

function dequeue() {
  return pending.shift();
}

function size() {
  return pending.length;
}

module.exports = { enqueue, dequeue, size };
