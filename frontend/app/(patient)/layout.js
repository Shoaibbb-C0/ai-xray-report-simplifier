import { requirePatient } from '@/lib/supabase/server';
import PatientNav from '@/components/auth/PatientNav';
import { supabaseConfig } from '@/lib/supabase/config';
export const dynamic = 'force-dynamic';
export default async function PatientLayout({ children }) {
  const configured = Boolean(supabaseConfig());
  if (configured) await requirePatient();
  return <main className="patient-shell">{configured && <PatientNav />}{children}</main>;
}
