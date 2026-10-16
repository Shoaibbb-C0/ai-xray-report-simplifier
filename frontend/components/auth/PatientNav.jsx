'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/client';
import { copy } from '@/lib/patient-copy';

export default function PatientNav() {
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const client = createClient();
    const { data } = client.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_OUT') window.location.replace('/login');
    });
    return () => data.subscription.unsubscribe();
  }, []);
  async function logout() {
    setBusy(true);
    try {
      const { error } = await createClient().auth.signOut();
      if (error) { setMessage(copy.logoutError); return; }
      window.location.replace('/login');
    } catch { setMessage(copy.logoutError); } finally { setBusy(false); }
  }
  return <><nav className="patient-nav" aria-label="Patient navigation"><Link href="/">AI X-Ray</Link><Link href="/map">{copy.map}</Link><Link href="/history">{copy.history}</Link><button onClick={logout} disabled={busy}>{copy.logout}</button></nav><p role="status">{message}</p></>;
}
