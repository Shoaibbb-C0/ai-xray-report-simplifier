import AuthForm from '@/components/auth/AuthForm';
import { supabaseConfig } from '@/lib/supabase/config';
export const dynamic = 'force-dynamic';
export default function Login() { return <AuthForm configured={Boolean(supabaseConfig())} />; }
