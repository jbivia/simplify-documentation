const test = require('node:test');
const assert = require('node:assert');
const { sum, echo } = require('../src/workers/handlers');

// These tests share the SQLite file, so they must not run concurrently.
// npm test pins --test-concurrency=1 for that reason.

test('sum adds the numbers', async () => {
  assert.deepStrictEqual(await sum({ numbers: [1, 2, 3] }), { total: 6 });
});

test('sum rejects a non-array payload', async () => {
  await assert.rejects(() => sum({ numbers: 'nope' }));
});

test('echo returns its payload', async () => {
  assert.deepStrictEqual(await echo({ a: 1 }), { a: 1 });
});
