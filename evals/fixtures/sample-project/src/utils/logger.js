const LEVELS = { debug: 10, info: 20, error: 30 };
const threshold = LEVELS[process.env.LOG_LEVEL || 'info'] ?? LEVELS.info;

function log(level, message) {
  if (LEVELS[level] < threshold) return;
  console.log(`[${level}] ${message}`);
}

module.exports = { log };
