import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router';
import type { Restaurant } from '../../domain/models';
import { formatNumber } from '../formatters';
import { FoodIllustration } from './food-illustration';
import { RestaurantFacts } from './restaurant-facts';

export function RestaurantCard({ restaurant }: { restaurant: Restaurant }) {
  return <article className="catalog-restaurant-card">
    <Link to={`/restaurants/${encodeURIComponent(restaurant.id)}`} className="catalog-restaurant-link" aria-label={`شوف قائمة ${restaurant.name}`}>
      <div className={`catalog-card-art catalog-art-${restaurant.artwork}`}>
        <span className="catalog-menu-count">{formatNumber(restaurant.meals.length)} أكلات</span>
        <FoodIllustration kind={restaurant.artwork} />
      </div>
      <div className="catalog-card-body">
        <div className="catalog-card-title"><h3>{restaurant.name}</h3><span className="catalog-card-arrow"><ArrowLeft size={20} aria-hidden="true" /></span></div>
        <p>{restaurant.cuisine}</p>
        <RestaurantFacts restaurant={restaurant} />
      </div>
    </Link>
  </article>;
}
