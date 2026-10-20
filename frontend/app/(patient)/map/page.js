import { requirePatient } from '@/lib/supabase/server';
import { getUserScans } from '@/services/scans';
import ScanHistory from '@/components/history/ScanHistory';
import { copy } from '@/lib/patient-copy';
import { supabaseConfig } from '@/lib/supabase/config';
import OfflineHistory from '@/components/OfflineHistory';
export default async function MapPage() {
  if (!supabaseConfig()) return <OfflineHistory map />;
  const { client, user } = await requirePatient();
  let scans;
  try { scans = await getUserScans(client, user.id); } catch { return <p role="alert">{copy.loadError}</p>; }
  return <ScanHistory scans={scans} map />;
}
