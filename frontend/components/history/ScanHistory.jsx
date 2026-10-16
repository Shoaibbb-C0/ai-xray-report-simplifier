'use client';
import { useState } from 'react';
import Link from 'next/link';
import BodyMap from '@/components/xray-map/BodyMap';
import { BODY_PARTS, filterScans, getBodyPartCounts, getLatestScanByBodyPart } from '@/services/scans';
import { copy } from '@/lib/patient-copy';

export default function ScanHistory({ scans, map = false, initialPart = 'all' }) {
  const [selected, setSelected] = useState(BODY_PARTS.includes(initialPart) ? initialPart : 'all');
  const counts = getBodyPartCounts(scans);
  const visible = filterScans(scans, selected);
  const latest = getLatestScanByBodyPart(scans, selected);
  return <>
    <h1>{map ? copy.map : copy.history}</h1>
    <p>{copy.modelNotice}</p>
    <div className={map ? 'map-history-grid' : ''}>
      {map && <BodyMap counts={counts} selected={selected} onSelect={setSelected} />}
      <section aria-label={copy.history} className="patient-stack">
        <div className="region-filters" role="group" aria-label={copy.regionFilter}>
          {['all', ...BODY_PARTS].map(part => <button key={part} aria-pressed={selected === part} onClick={() => setSelected(part)}>
            {part === 'all' ? copy.all : copy.regions[part]} ({part === 'all' ? scans.length : counts[part]})
          </button>)}
        </div>
        <p aria-live="polite">{visible.length} {copy.count}{latest ? ` · ${copy.latest}: ${latest.scan_date}` : ''}</p>
        {!visible.length && <p className="patient-panel">{copy.empty}</p>}
        <ol className="patient-stack">
          {visible.map(scan => {
            const result = Array.isArray(scan.analysis_results) ? scan.analysis_results[0] : scan.analysis_results;
            return <li key={scan.id} className="patient-panel">
              <div className="scan-placeholder" aria-hidden="true">◇</div>
              <h2>{copy.regions[scan.body_part] || copy.regions.unknown}</h2>
              <p><time dateTime={scan.scan_date}>{scan.scan_date}</time> · {scan.body_side || copy.sideMissing}</p>
              <p>{result?.analysis_status?.replaceAll('_', ' ') || scan.status}</p>
              <p>{result?.fracture_result?.replaceAll('_', ' ') || copy.pending}</p>
              <p className="break-words">{result && Object.values(result.model_versions || {}).join(' · ')}</p>
              <Link href={`/history/${scan.id}`}>{copy.detail}</Link>
            </li>;
          })}
        </ol>
      </section>
    </div>
  </>;
}
