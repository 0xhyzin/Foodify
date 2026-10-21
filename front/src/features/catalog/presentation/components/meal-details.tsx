import type { Meal } from '../../domain/models';
import { Dialog } from '@/shared/ui/dialog';
import { Button } from '@/shared/ui/button';
import { formatPrice } from '../formatters';
import { FoodIllustration } from './food-illustration';

export function MealDetails({ meal, onClose }: { meal: Meal | undefined; onClose(): void }) {
  return <Dialog open={Boolean(meal)} title={meal?.name || 'تفاصيل الوجبة'} onClose={onClose}>
    {meal && <div className="catalog-meal-details">
      <div className={`catalog-detail-art catalog-art-${meal.artwork}`}><FoodIllustration kind={meal.artwork} /></div>
      <p>{meal.description}</p>
      <h3>المكونات</h3><ul>{meal.ingredients.map(ingredient => <li key={ingredient}>{ingredient}</li>)}</ul>
      <div className="catalog-detail-price"><span>السعر التجريبي</span><strong>{formatPrice(meal.price)}</strong></div>
      <p className="catalog-demo-caption">دي وجبة ديمو للعرض. مفيش طلب أو دفع فعلي.</p>
      <Button onClick={onClose}>رجوع للقائمة</Button>
    </div>}
  </Dialog>;
}
