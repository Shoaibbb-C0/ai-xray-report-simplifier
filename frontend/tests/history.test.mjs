// DEMO / TEST DATA. Never imported by the application or seeded remotely.
import test from 'node:test';
import assert from 'node:assert/strict';
import { canonicalBodyPart, filterScans, getBodyPartCounts, getLatestScanByBodyPart, getUserScans, getScanById } from '../services/scans.js';
import { authState, isPatientRoute, safeReturnPath } from '../lib/auth.js';
import { ensureProfile, getProfile } from '../services/profiles.js';

const scans = [
  { body_part: 'hand', scan_date: '2026-01-01', created_at: '2026-01-01', body_side: null },
  { body_part: 'hand', scan_date: '2026-02-01', created_at: '2026-02-01', body_side: 'left' },
  { body_part: 'mixed', scan_date: '2026-03-01', created_at: '2026-03-01' },
  { body_part: 'unexpected', scan_date: '2026-01-01', created_at: '2026-01-01' },
];

test('canonical regions, unknown/mixed, filters, latest and counts preserve side', () => {
  assert.equal(canonicalBodyPart(' HAND '), 'hand');
  assert.equal(canonicalBodyPart('left_hand'), 'unknown');
  assert.equal(canonicalBodyPart(null), 'unknown');
  assert.equal(filterScans(scans, 'hand').length, 2);
  assert.equal(filterScans(scans, 'mixed').length, 1);
  assert.equal(filterScans(scans, 'unknown').length, 1);
  assert.deepEqual(getBodyPartCounts(scans), { hand: 2, leg: 0, hip: 0, shoulder: 0, mixed: 1, unknown: 1 });
  assert.equal(getLatestScanByBodyPart(scans, 'hand').scan_date, '2026-02-01');
  assert.equal(getLatestScanByBodyPart(scans, 'leg'), null);
  assert.equal(scans[0].body_side, null);
});

test('auth helpers deny anonymous state and unsafe return URLs', () => {
  assert.equal(authState(null), 'anonymous');
  assert.equal(authState({ user: { id: 'test' } }), 'authenticated');
  for (const path of ['/map', '/history', '/history/abc', '/profile']) assert.ok(isPatientRoute(path));
  assert.equal(isPatientRoute('/history-public'), false);
  for (const path of ['https://evil.example', '//evil.example', '/\\evil', '/login', null]) assert.equal(safeReturnPath(path), '/map');
  assert.equal(safeReturnPath('/history/abc'), '/history/abc');
});

function mockClient(data = [], error = null) {
  const calls = [];
  const query = Object.fromEntries(['select', 'eq', 'order', 'range', 'maybeSingle', 'upsert'].map(name => [name, (...args) => { calls.push([name, ...args]); return query; }]));
  query.then = resolve => Promise.resolve({ data, error }).then(resolve);
  return { calls, from: table => { calls.push(['from', table]); return query; } };
}

test('repository scopes user and region, handles empty history and missing details', async () => {
  const client = mockClient([]);
  assert.deepEqual(await getUserScans(client, 'user-a', 'HAND'), []);
  assert.ok(client.calls.some(call => JSON.stringify(call) === JSON.stringify(['eq', 'user_id', 'user-a'])));
  assert.ok(client.calls.some(call => JSON.stringify(call) === JSON.stringify(['eq', 'body_part', 'hand'])));
  assert.equal(await getScanById(client, 'user-a', 'bad-id'), null);
  await assert.rejects(getUserScans(client, null), /Authentication/);
  await assert.rejects(getScanById(client, null, 'bad-id'), /Authentication/);
  await assert.rejects(getUserScans(mockClient(null, { message: 'private server error' }), 'user-a'), /History unavailable/);
});

test('profile initialization is owner scoped and never overwrites existing preferences', async () => {
  const client = mockClient({ id: 'user-a' });
  await ensureProfile(client, 'user-a');
  assert.ok(client.calls.some(call => call[0] === 'upsert' && call[1].id === 'user-a' && call[2].ignoreDuplicates));
  assert.equal((await getProfile(client, 'user-a')).id, 'user-a');
  await assert.rejects(ensureProfile(client, null), /Authentication/);
});

test('detail repository includes both ownership and ID filters', async () => {
  const id = '00000000-0000-4000-8000-000000000001';
  const client = mockClient({ id });
  assert.equal((await getScanById(client, 'user-a', id)).id, id);
  assert.ok(client.calls.some(call => call[0] === 'eq' && call[1] === 'user_id' && call[2] === 'user-a'));
  assert.ok(client.calls.some(call => call[0] === 'eq' && call[1] === 'id' && call[2] === id));
});
