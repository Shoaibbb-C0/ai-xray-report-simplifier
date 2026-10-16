'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/client';
import { safeReturnPath } from '@/lib/auth';
import { copy } from '@/lib/patient-copy';
import { ensureProfile } from '@/services/profiles';

export default function AuthForm({ signup = false, configured }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get('verification') === 'failed') setMessage(copy.verificationFailed);
  }, []);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setMessage('');
    const form = new FormData(event.currentTarget);
    try {
      const client = createClient();
      const credentials = { email: form.get('email'), password: form.get('password') };
      const { data, error } = signup
        ? await client.auth.signUp({ ...credentials, options: { emailRedirectTo: `${window.location.origin}/auth/callback` } })
        : await client.auth.signInWithPassword(credentials);
      if (error) { setMessage(copy.authError); return; }
      if (signup && !data.session) { setMessage(copy.verify); return; }
      try { await ensureProfile(client, data.user.id); }
      catch { setMessage(copy.profileError); return; }
      window.location.assign(safeReturnPath(new URLSearchParams(window.location.search).get('next')));
    } catch { setMessage(copy.authError); } finally { setBusy(false); }
  }
  return <main className="patient-shell auth-shell">
    <Link href="/">AI X-Ray</Link>
    <h1>{signup ? copy.signup : copy.login}</h1>
    {!configured && <p role="status">{copy.setup}</p>}
    <form onSubmit={submit} className="patient-stack">
      <label>{copy.email}<input name="email" type="email" autoComplete="email" required maxLength={254} /></label>
      <label>{copy.password}<input name="password" type="password" autoComplete={signup ? 'new-password' : 'current-password'} minLength={signup ? 12 : undefined} maxLength={128} required /></label>
      <button disabled={busy || !configured}>{busy ? copy.wait : signup ? copy.signup : copy.login}</button>
      <p role="status" aria-live="polite">{message}</p>
    </form>
    <Link href={signup ? '/login' : '/signup'}>{signup ? copy.login : copy.signup}</Link>
  </main>;
}
