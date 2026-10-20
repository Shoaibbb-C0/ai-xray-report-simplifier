// Explicit future-connected action. Never called during database-absent analysis.
import { canonicalBodyPart } from './scans.js';

export async function saveAnalysis(client, file, result) {
  const { data, error: authError } = await client.auth.getUser();
  if (authError || !data.user) throw new Error('Sign in before saving to your history.');
  if (!result?.explanation || !['image/png', 'image/jpeg'].includes(file?.type)) throw new Error('Analyze a supported image before saving.');
  const userId = data.user.id;
  const scanId = crypto.randomUUID();
  const path = `${userId}/${scanId}/image.${file.type === 'image/png' ? 'png' : 'jpg'}`;
  const explanation = structuredClone(result.explanation);
  // Persist the Stage 5 result, never regenerate its meaning in JavaScript.
  explanation.attention = { ...explanation.attention, available: false, overlay_base64: null, overlay_path: null };
  const scan = { id: scanId, user_id: userId, scan_date: new Date().toISOString().slice(0, 10),
    body_part: canonicalBodyPart(explanation.body_part?.id), body_side: null,
    mime_type: file.type, storage_path: path, status: 'pending' };
  const inserted = await client.from('xray_scans').insert(scan);
  if (inserted.error) throw new Error('Your scan could not be saved.');
  let uploaded = false;
  try {
    const stored = await client.storage.from('xray-scans').upload(path, file, { contentType: file.type, upsert: false });
    if (stored.error) throw stored.error;
    uploaded = true;
    const analysis = { scan_id: scanId, user_id: userId, analysis_status: explanation.analysis_status,
      explanation, model_versions: result.model_versions || explanation.model_versions || {},
      xray_validation_result: result.xray_validation?.result || null,
      xray_validation_confidence: result.xray_validation?.confidence ?? null,
      body_part_result: result.body_part?.result || 'unknown', body_part_confidence: result.body_part?.confidence ?? null,
      fracture_result: result.abnormality?.result || 'not_analyzed', fracture_confidence: result.abnormality?.confidence ?? null };
    const analyzed = await client.from('analysis_results').insert(analysis);
    if (analyzed.error) throw analyzed.error;
    const completed = await client.from('xray_scans').update({ status: 'complete' }).eq('id', scanId).eq('user_id', userId);
    if (completed.error) throw completed.error;
    return scanId;
  } catch {
    if (uploaded) {
      const removed = await client.storage.from('xray-scans').remove([path]);
      if (removed.error) throw new Error('Saving failed and cleanup needs attention. Your pending scan remains in history so its private file can be recovered.');
    }
    const cleaned = await client.from('xray_scans').delete().eq('id', scanId).eq('user_id', userId);
    if (cleaned.error) throw new Error('Saving failed. A pending scan remains in your history for cleanup.');
    throw new Error('Your scan could not be saved. No completed history record was created.');
  }
}
