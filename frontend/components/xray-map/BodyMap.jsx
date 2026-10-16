'use client';
import { copy } from '@/lib/patient-copy';

// Original application-owned standardized skeleton. Bilateral targets deliberately
// use coarse region IDs: visual position is never persisted as inferred laterality.
const targets = [
  ['shoulder', 98, 116], ['shoulder', 222, 116],
  ['hand', 58, 298], ['hand', 262, 298],
  ['hip', 135, 275], ['hip', 185, 275],
  ['leg', 130, 397], ['leg', 190, 397],
];

export default function BodyMap({ counts, selected, onSelect }) {
  return <figure className="body-map">
    <svg viewBox="0 0 320 540" role="group" aria-labelledby="body-map-title body-map-desc">
      <title id="body-map-title">{copy.map}</title>
      <desc id="body-map-desc">{copy.mapNotice}</desc>
      <g fill="#192b38" stroke="#607d8b" strokeWidth="2">
        <path d="M137 80 Q108 91 94 112 L72 215 48 299 Q45 322 62 324 L91 226 113 161 119 250 Q107 275 119 309 L115 410 108 502 Q104 522 132 520 L145 414 160 320 175 414 188 520 Q216 522 212 502 L205 410 201 309 Q213 275 201 250 L207 161 229 226 258 324 Q275 322 272 299 L248 215 226 112 Q212 91 183 80Z" />
        <ellipse cx="160" cy="46" rx="29" ry="35" />
      </g>
      <g fill="none" stroke="#c3d8df" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M160 85V258 M160 111L108 119 87 212 67 282 M160 111L212 119 233 212 253 282 M126 282L134 386 122 492 M194 282L186 386 198 492" />
        <path d="M125 258Q160 290 195 258L190 288 160 314 130 288Z" />
        {[139, 158, 177, 196, 215].map((y, i) => <path key={y} strokeWidth="4" d={`M151 ${y} Q${112 + i * 3} ${y - 16} ${119 + i * 3} ${y + 4} Q139 ${y + 15} 151 ${y + 9} M169 ${y} Q${208 - i * 3} ${y - 16} ${201 - i * 3} ${y + 4} Q181 ${y + 15} 169 ${y + 9}`} />)}
        <path d="M111 508H128 M192 508H209 M58 302L53 315 M65 302L62 319 M255 302L258 319 M262 302L267 315" strokeWidth="4" />
      </g>
      {targets.map(([part, x, y], i) => <g key={i} role="button" tabIndex={0}
        aria-label={`${copy.regions[part]}: ${counts[part]} ${copy.count}`}
        aria-pressed={selected === part} className="map-target"
        onClick={() => onSelect(part)} onKeyDown={event => {
          if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(part); }
        }}>
        <circle cx={x} cy={y} r="24" fill={selected === part ? '#0f766e' : '#123843'} stroke="#5eead4" strokeWidth="2" />
        <text x={x} y={y + 5} textAnchor="middle" fill="white" fontSize="14" aria-hidden="true">{counts[part]}</text>
      </g>)}
    </svg>
    <figcaption>{copy.mapNotice}</figcaption>
  </figure>;
}
