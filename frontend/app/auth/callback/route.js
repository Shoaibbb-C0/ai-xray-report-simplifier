import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { ensureProfile } from '@/services/profiles';
export async function GET(request) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const client = createClient();
  if (code && client) {
    const { error } = await client.auth.exchangeCodeForSession(code);
    if (!error) {
      const { data } = await client.auth.getUser();
      if (data.user) {
        try { await ensureProfile(client, data.user.id); }
        catch { return NextResponse.redirect(new URL('/login?verification=failed', url.origin)); }
        return NextResponse.redirect(new URL('/map', url.origin));
      }
    }
  }
  return NextResponse.redirect(new URL('/login?verification=failed', url.origin));
}
