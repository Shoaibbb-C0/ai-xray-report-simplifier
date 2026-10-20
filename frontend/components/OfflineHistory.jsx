import Link from 'next/link';
import ScanHistory from '@/components/history/ScanHistory';
export default function OfflineHistory({ map = false }) {
  return <><div className="offline-notice"><strong>Your history starts with you.</strong><p>Accounts and saved scans are not connected in this local version. {map && 'Explore the map below. '}Every count is zero because no scans have been saved. Analysis is available without an account.</p><Link href="/">Understand an X-ray →</Link></div><ScanHistory scans={[]} map={map} /></>;
}
