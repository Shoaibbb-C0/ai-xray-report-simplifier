const { PHASE_DEVELOPMENT_SERVER } = require('next/constants');

// A dev server and a production preview must never rewrite each other's chunks.
module.exports = phase => ({
  reactStrictMode: true,
  distDir: phase === PHASE_DEVELOPMENT_SERVER ? '.next' : '.next-production',
});
