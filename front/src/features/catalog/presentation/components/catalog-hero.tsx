import { ArrowDown, UtensilsCrossed } from 'lucide-react';
import { FoodIllustration } from './food-illustration';

export function CatalogHero() {
  function browseRestaurants() {
    const heading = document.getElementById('restaurants-heading');
    heading?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
    heading?.focus({ preventScroll: true });
  }

  return <section className="catalog-hero" aria-labelledby="catalog-heading">
    <div className="catalog-hero-copy">
      <span className="catalog-eyebrow"><UtensilsCrossed size={16} aria-hidden="true" />حاجة حلوة لكل مزاج</span>
      <h1 id="catalog-heading" tabIndex={-1}>جعان؟<br />اختار اللي على مزاجك.</h1>
      <p>مطاعم مختلفة، وأكلات تحبها.<br />لفّ في القوائم وشوف وجبتك الجاية.</p>
      <button type="button" className="catalog-browse-button" onClick={browseRestaurants}>شوف المطاعم<ArrowDown size={18} aria-hidden="true" /></button>
    </div>
    <div className="catalog-hero-art" aria-hidden="true"><div className="catalog-hero-orbit" /><FoodIllustration kind="burger" /><span className="catalog-hero-sticker">مزاجك،<br />في أول لقمة.</span></div>
  </section>;
}
