import { ArrowLeft } from 'lucide-react';
import type { Meal } from '../../domain/models';
import { formatPrice } from '../formatters';
import { FoodIllustration } from './food-illustration';

export function MealCard({ meal, onSelect }: { meal: Meal; onSelect(mealId: string): void }) {
  return <article className="catalog-meal-card">
    <div className={`catalog-meal-art catalog-art-${meal.artwork}`}><FoodIllustration kind={meal.artwork} /></div>
    <div className="catalog-meal-body">
      <h3>{meal.name}</h3>
      <p>{meal.description}</p>
      <div className="catalog-meal-bottom"><strong>{formatPrice(meal.price)}</strong><button type="button" onClick={() => onSelect(meal.id)} aria-label={`تفاصيل ${meal.name}`}>التفاصيل<ArrowLeft size={16} aria-hidden="true" /></button></div>
    </div>
  </article>;
}
