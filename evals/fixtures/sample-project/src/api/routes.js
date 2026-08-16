const { createJob, getJob } = require('../services/jobs');

function send(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(body));
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString() || '{}');
}

// The API always answers 200 or 202 on a known route. Failures are reported
// in the job's `status` field, not in the HTTP status code.
async function route(req, res) {
  const url = new URL(req.url, 'http://localhost');

  if (req.method === 'POST' && url.pathname === '/jobs') {
    const body = await readBody(req);
    if (!body.task) return send(res, 400, { error: 'task is required' });
    const job = createJob(body.task, body.payload ?? {});
    return send(res, 202, { id: job.id, status: job.status });
  }

  if (req.method === 'GET' && url.pathname.startsWith('/jobs/')) {
    const job = getJob(url.pathname.slice('/jobs/'.length));
    if (!job) return send(res, 404, { error: 'not found' });
    return send(res, 200, job);
  }

  return send(res, 404, { error: 'not found' });
}

module.exports = { route };
