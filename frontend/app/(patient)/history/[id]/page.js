import Link from 'next/link';
import { notFound } from 'next/navigation';
import { requirePatient } from '@/lib/supabase/server';
import { getScanById } from '@/services/scans';
import { copy } from '@/lib/patient-copy';
import ExplanationCard from '@/components/explanation/ExplanationCard';
import AnatomicalIllustration from '@/components/explanation/AnatomicalIllustration';
import { supabaseConfig } from '@/lib/supabase/config';

export default async function ScanPage({ params }) {
  if (!supabaseConfig()) notFound();
  const { id } = await params;
  const { client, user } = await requirePatient();
  let scan;
  try { scan = await getScanById(client, user.id, id); } catch { return <p role="alert">{copy.loadError}</p>; }
  if (!scan) notFound();
  const result = Array.isArray(scan.analysis_results) ? scan.analysis_results[0] : scan.analysis_results;
  const explanation = result?.explanation;
  const visual = explanation?.visual;
  // Only repository-owned educational artwork. Never render stored remote/private paths.
  const illustration = /^\/assets\/anatomy\/(hand|leg|hip|shoulder|common)\/[a-z_]+\.svg$/.test(visual?.illustration_url || '') ? visual.illustration_url : null;
  return <article className="patient-stack">
    <Link href="/history">{copy.history}</Link>
    <h1>{copy.regions[scan.body_part]} · {scan.scan_date}</h1>
    <p>{copy.modelNotice}</p>
    <dl className="patient-panel metadata-grid">
      <dt>{copy.scanStatus}</dt><dd>{scan.status}</dd>
      <dt>{copy.sideSupplied}</dt><dd>{scan.body_side || copy.notSupplied}</dd>
      <dt>{copy.analysisStatus}</dt><dd>{result?.analysis_status || copy.pending}</dd>
      <dt>{copy.fractureResult}</dt><dd>{result?.fracture_result || copy.notAnalyzed}</dd>
      {result?.fracture_confidence != null && <><dt>{copy.confidenceLabel}</dt><dd>{(result.fracture_confidence * 100).toFixed(1)}% — {copy.confidence}</dd></>}
      <dt>{copy.models}</dt><dd className="break-words">{JSON.stringify(result?.model_versions || {})}</dd>
    </dl>
    {explanation ? <ExplanationCard explanation={explanation} /> : <p>{copy.pending}</p>}
    {illustration && <AnatomicalIllustration illustrationUrl={illustration} title={visual.title} altText={visual.alt_text} labelNotice={visual.label_notice} />}
    {explanation?.attention && <section className="patient-panel"><h2>{copy.attention}</h2><p>{explanation.attention.disclaimer}</p><p>{copy.attentionPending}</p></section>}
    {explanation?.localization && <p>{explanation.localization.reason}</p>}
  </article>;
}
