import AuthForm from '@/components/auth/AuthForm';
import { supabaseConfig } from '@/lib/supabase/config';
export const dynamic = 'force-dynamic';
export default function Signup() { return <AuthForm signup configured={Boolean(supabaseConfig())} />; }
