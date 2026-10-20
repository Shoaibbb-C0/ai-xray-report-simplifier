export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
export function validateFile(file) {
  if (!file) return 'Choose an X-ray image to continue.';
  if (!['image/jpeg', 'image/png'].includes(file.type)) return 'Choose a JPG, JPEG or PNG image.';
  if (!file.size || file.size > MAX_UPLOAD_BYTES) return 'Choose an image smaller than 10 MiB.';
  return null;
}

export async function analyzeImage(file, { language = 'en', attention = false, signal } = {}) {
  const form = new FormData();
  form.append('file', file);
  form.append('language', language);
  form.append('attention', String(attention));
  const base = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001').replace(/\/$/, '');
  let response;
  try { response = await fetch(`${base}/api/v1/analyze`, { method: 'POST', body: form, signal }); }
  catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('The local analysis server could not be reached. Start the backend and try again.');
  }
  let result;
  try { result = await response.json(); }
  catch { throw new Error('The server returned an unreadable response. Please try again.'); }
  if (!response.ok) {
    const error = new Error(result.detail?.message || 'The image could not be analyzed. Please try again.');
    error.code = result.detail?.code || 'request_failed';
    throw error;
  }
  return result;
}
