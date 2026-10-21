import type { FoodKind } from '../../domain/models';

/** Local vector artwork keeps the demo self-contained and matches the brand palette. */
export function FoodIllustration({ kind }: { kind: FoodKind }) {
  return <svg className="catalog-food-art" viewBox="0 0 240 180" fill="none" aria-hidden="true">
    <ellipse cx="120" cy="157" rx="83" ry="11" fill="currentColor" opacity=".08" />
    <circle cx="120" cy="89" r="75" fill="white" opacity=".48" />
    <g stroke="#171719" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      {kind === 'burger' && <>
        <path d="M48 83c3-37 31-57 72-57s69 20 72 57H48Z" fill="white" />
        <path d="m51 91 23 9 22-9 24 9 24-9 23 9 22-9" stroke="var(--red)" strokeWidth="8" />
        <rect x="47" y="105" width="146" height="20" rx="10" fill="#171719" />
        <path d="m69 121 30 15 29-15" fill="var(--red)" stroke="var(--red)" />
        <path d="M48 139h144c-3 14-11 18-27 18H75c-16 0-24-4-27-18Z" fill="white" />
        <path d="m85 54 5-4m28-9 5 2m28 8 4 5m-50 9 5 2m28-3 5-4" stroke="var(--red)" strokeWidth="4" />
      </>}
      {kind === 'pizza' && <>
        <circle cx="120" cy="91" r="65" fill="white" />
        <circle cx="120" cy="91" r="53" fill="var(--red)" stroke="var(--red)" />
        <path d="m120 91 4-52m-4 52 48 22m-48-22-45 30" stroke="white" strokeWidth="3" />
        <g fill="white" stroke="white"><circle cx="97" cy="65" r="8" /><circle cx="145" cy="72" r="8" /><circle cx="122" cy="120" r="8" /><circle cx="85" cy="99" r="6" /><circle cx="151" cy="111" r="6" /></g>
        <path d="m115 63-3 7m19 26 6-2m-27 4-5 4" stroke="#171719" strokeWidth="5" />
      </>}
      {kind === 'bowl' && <>
        <ellipse cx="120" cy="92" rx="73" ry="24" fill="white" />
        <path d="M47 92c6 43 30 65 73 65s67-22 73-65c-33 28-111 28-146 0Z" fill="white" />
        <ellipse cx="120" cy="88" rx="57" ry="14" fill="var(--red)" stroke="var(--red)" />
        <path d="m86 85 6 3m17-10 4 5m14 9 6-3m16-6 5 4m-43 9 5-3" stroke="white" />
        <path d="M95 48c-12-12 9-15 0-28m25 29c-12-12 9-15 0-28m25 27c-12-12 9-15 0-28" stroke="var(--red)" opacity=".6" />
        <path d="M94 139h52" stroke="var(--red)" />
      </>}
      {kind === 'wrap' && <g transform="rotate(-19 120 90)">
        <path d="M77 58c-5-28 86-28 85 0l-10 91c-11 15-51 15-63 0L77 58Z" fill="white" />
        <ellipse cx="120" cy="54" rx="42" ry="20" fill="var(--red)" />
        <path d="m94 53 10-7 11 10 12-12 14 8" stroke="white" strokeWidth="5" />
        <path d="m83 90 72 19m-70 2 67 18" stroke="var(--red)" opacity=".5" />
        <path d="m89 121 33 14 31-14-2 31c-17 12-44 12-60-1l-2-30Z" fill="var(--red)" stroke="var(--red)" />
        <path d="m116 147 4-5 4 5" stroke="white" />
      </g>}
    </g>
  </svg>;
}
