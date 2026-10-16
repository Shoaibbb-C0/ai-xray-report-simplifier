import { createServerClient } from '@supabase/ssr';
import { NextResponse } from 'next/server';
import { supabaseConfig } from './lib/supabase/config';
import { isPatientRoute } from './lib/auth';

export async function middleware(request) {
  let response = NextResponse.next({ request });
  response.headers.set('Cache-Control', 'private, no-store');
  const config = supabaseConfig();
  const protectedRoute = isPatientRoute(request.nextUrl.pathname);
  let user = null;
  if (config) {
    const client = createServerClient(config.url, config.key, { cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(values) {
        values.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        response.headers.set('Cache-Control', 'private, no-store');
        values.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    }});
    try { const { data } = await client.auth.getUser(); user = data.user; } catch { /* Fail closed. */ }
  }
  if (protectedRoute && !user) {
    const url = new URL('/login', request.url);
    url.searchParams.set('next', request.nextUrl.pathname);
    if (!config) url.searchParams.set('setup', 'required');
    const redirect = NextResponse.redirect(url);
    response.cookies.getAll().forEach(cookie => redirect.cookies.set(cookie));
    redirect.headers.set('Cache-Control', 'private, no-store');
    return redirect;
  }
  return response;
}

export const config = { matcher: ['/map/:path*', '/history/:path*', '/profile/:path*', '/login', '/signup', '/auth/:path*'] };
