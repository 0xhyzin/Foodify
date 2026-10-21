import { Clock3, Bike, Star } from 'lucide-react';
import type { Restaurant } from '../../domain/models';
import { formatNumber, formatPrice } from '../formatters';

export function RestaurantFacts({ restaurant }: { restaurant: Restaurant }) {
  return <ul className="catalog-facts" aria-label="تفاصيل المطعم التجريبية">
    <li><Star size={15} aria-hidden="true" /><span aria-label={`التقييم ${restaurant.rating} من 5`}>{formatNumber(restaurant.rating)}</span></li>
    <li><Clock3 size={15} aria-hidden="true" /><span><bdi>{restaurant.deliveryMinutes}</bdi> دقيقة</span></li>
    <li><Bike size={16} aria-hidden="true" /><span>توصيل {formatPrice(restaurant.deliveryFee)}</span></li>
  </ul>;
}
