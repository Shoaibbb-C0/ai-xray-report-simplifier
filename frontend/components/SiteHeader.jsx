import Link from 'next/link';
export default function SiteHeader() {
  return <><a className="skip-link" href="#main-content">Skip to content</a><header className="site-header"><Link className="wordmark" href="/" aria-label="AI X-Ray home"><span className="brand-emblem" aria-hidden="true">x</span>AI X-Ray<span className="brand-detail">A clearer picture.</span></Link><nav aria-label="Main navigation"><Link href="/">Understand an X-ray</Link><Link href="/map">My X-Ray Map</Link><Link href="/history">History</Link></nav><Link className="account-link" href="/login">Your account <span aria-hidden="true">↗</span></Link></header></>;
}
