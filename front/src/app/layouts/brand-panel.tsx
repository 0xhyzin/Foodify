import { Heart, Sandwich, ShoppingBasket } from 'lucide-react';
export function BrandPanel() {
  return <aside className="brand-panel" aria-label="Foodify: أكل ومقاضي على بابك">
    <div className="brand-kicker">يومك يستاهل يبقى أسهل</div>
    <h2>أكلك ومقاضيك،<br />على بابك.</h2>
    <p>حساب واحد لكل اللي بتحبّه.<br />خلّي التفاصيل علينا، واستمتع بيومك.</p>
    <div className="brand-art" aria-hidden="true"><div className="art-ring" /><div className="art-bag"><span>foodify</span><i /><small>شوية راحة ليومك.</small></div><div className="art-chip chip-food"><Sandwich size={29} /></div><div className="art-chip chip-grocery"><ShoppingBasket size={29} /></div></div>
    <div className="brand-foot"><Heart size={17} />تفاصيل أقل. راحة أكتر.</div>
  </aside>;
}
