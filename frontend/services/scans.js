export const BODY_PARTS = ['hand', 'leg', 'hip', 'shoulder', 'mixed', 'unknown'];
export const SCAN_COLUMNS = 'id,user_id,created_at,scan_date,body_part,body_side,status,analysis_results(id,analysis_status,fracture_result,fracture_confidence,model_versions)';

export function canonicalBodyPart(value) {
  const part = typeof value === 'string' ? value.trim().toLowerCase() : '';
  return BODY_PARTS.includes(part) ? part : 'unknown';
}

export function filterScans(scans, part = 'all') {
  return part === 'all' ? scans : scans.filter(scan => canonicalBodyPart(scan.body_part) === canonicalBodyPart(part));
}

export function getBodyPartCounts(scans) {
  return scans.reduce((counts, scan) => {
    counts[canonicalBodyPart(scan.body_part)]++;
    return counts;
  }, Object.fromEntries(BODY_PARTS.map(part => [part, 0])));
}

export function getLatestScanByBodyPart(scans, part) {
  return filterScans(scans, part).slice().sort((a, b) => b.scan_date.localeCompare(a.scan_date) || b.created_at.localeCompare(a.created_at))[0] || null;
}

export async function getUserScans(client, userId, part = 'all') {
  if (!userId) throw new Error('Authentication required');
  // Fetch all pages: PostgREST has a default 1,000-row cap.
  const scans = [];
  for (let offset = 0; ; offset += 500) {
    let query = client.from('xray_scans').select(SCAN_COLUMNS).eq('user_id', userId);
    if (part !== 'all') query = query.eq('body_part', canonicalBodyPart(part));
    const { data, error } = await query.order('scan_date', { ascending: false }).order('id', { ascending: false }).range(offset, offset + 499);
    if (error) throw new Error('History unavailable');
    scans.push(...data);
    if (data.length < 500) return scans;
  }
}

export const getScansByBodyPart = (client, userId, part) => getUserScans(client, userId, part);

export async function getScanById(client, userId, id) {
  if (!userId) throw new Error('Authentication required');
  if (!/^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(id)) return null;
  const { data, error } = await client.from('xray_scans').select('*,analysis_results(*)').eq('user_id', userId).eq('id', id).maybeSingle();
  if (error) throw new Error('Scan unavailable');
  return data;
}
