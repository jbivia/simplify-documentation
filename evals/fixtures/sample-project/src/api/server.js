const http = require('node:http');
const { route } = require('./routes');
const { log } = require('../utils/logger');

const PORT = Number(process.env.PORT || 3000);

const server = http.createServer((req, res) => {
  route(req, res).catch((err) => {
    log('error', err.message);
    res.writeHead(500, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ error: 'internal' }));
  });
});

server.listen(PORT, () => log('info', `api listening on ${PORT}`));

module.exports = { server };
