import { requirePatient } from '@/lib/supabase/server';
import PatientNav from '@/components/auth/PatientNav';
export const dynamic = 'force-dynamic';
export default async function PatientLayout({ children }) {
  await requirePatient();
  return <main className="patient-shell"><PatientNav />{children}</main>;
}
