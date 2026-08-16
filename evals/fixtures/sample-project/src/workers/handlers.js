async function echo(payload) {
  return payload;
}

async function sum(payload) {
  if (!Array.isArray(payload.numbers)) throw new Error('numbers must be an array');
  return { total: payload.numbers.reduce((a, b) => a + b, 0) };
}

module.exports = { echo, sum };
