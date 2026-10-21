import { useState } from 'react';
import { SearchX, Store } from 'lucide-react';
import { demoRestaurants, restaurantCategories } from '../../data/restaurants.js';
import { filterRestaurants } from '../../application/filter-restaurants';
import type { CatalogCategory } from '../../domain/models';
import { Button } from '@/shared/ui/button';
import { CatalogHero } from '../components/catalog-hero';
import { CatalogFilters } from '../components/catalog-filters';
import { RestaurantCard } from '../components/restaurant-card';
import { formatNumber } from '../formatters';

export function RestaurantsPage() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<CatalogCategory>('all');
  const restaurants = filterRestaurants(demoRestaurants, query, category);

  return <>
    <CatalogHero />
    <section className="catalog-restaurants" aria-labelledby="restaurants-heading">
      <div className="catalog-section-heading"><div><span className="catalog-section-kicker"><Store size={15} aria-hidden="true" />اختيارك يبدأ هنا</span><h2 id="restaurants-heading" tabIndex={-1}>مطاعم على ذوقك</h2></div><span className="catalog-demo-label">قوائم تجريبية</span></div>
      <CatalogFilters categories={restaurantCategories} category={category} query={query} onCategoryChange={setCategory} onQueryChange={setQuery} />
      <p className="catalog-results-count" role="status" aria-live="polite">المطاعم المعروضة: {formatNumber(restaurants.length)}{query.trim() ? ` لبحث «${query.trim()}»` : ''} · ٣ أكلات في كل مطعم</p>
      <div id="restaurants-list">
        {restaurants.length > 0 ? <div className="catalog-restaurant-grid">{restaurants.map(restaurant => <RestaurantCard key={restaurant.id} restaurant={restaurant} />)}</div>
          : <div className="catalog-empty"><SearchX size={36} aria-hidden="true" /><h3>ملقيناش مطاعم بالاختيارات دي</h3><p>جرّب اسم أكلة تانية، أو ارجع شوف كل المطاعم.</p><Button variant="secondary" onClick={() => { setQuery(''); setCategory('all'); document.getElementById('restaurant-search')?.focus(); }}>عرض كل المطاعم</Button></div>}
      </div>
    </section>
  </>;
}
