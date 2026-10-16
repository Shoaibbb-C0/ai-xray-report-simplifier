import 'server-only';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { supabaseConfig } from './config';

export function createClient() {
  const config = supabaseConfig();
  if (!config) return null;
  const store = cookies();
  return createServerClient(config.url, config.key, {
    cookies: {
      getAll: () => store.getAll(),
      setAll(values) {
        // Middleware refreshes cookies when rendering a Server Component.
        try { values.forEach(({ name, value, options }) => store.set(name, value, options)); } catch {}
      },
    },
  });
}

export async function requirePatient() {
  const client = createClient();
  if (!client) redirect('/login?setup=required');
  const { data, error } = await client.auth.getUser();
  if (error || !data.user) redirect('/login');
  return { client, user: data.user };
}
