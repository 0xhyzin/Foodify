import { useState } from 'react';
import { Link, useParams } from 'react-router';
import { ArrowRight, ChefHat, Store } from 'lucide-react';
import { demoRestaurants } from '../../data/restaurants.js';
import { FoodIllustration } from '../components/food-illustration';
import { RestaurantFacts } from '../components/restaurant-facts';
import { MealCard } from '../components/meal-card';
import { MealDetails } from '../components/meal-details';
import { formatNumber } from '../formatters';

export function RestaurantPage() {
  const { restaurantId } = useParams();
  const restaurant = demoRestaurants.find(item => item.id === restaurantId);
  const [selectedMealId, setSelectedMealId] = useState<string | null>(null);

  if (!restaurant) return <div className="catalog-empty catalog-missing-restaurant"><Store size={40} aria-hidden="true" /><h1 tabIndex={-1}>المطعم ده مش موجود</h1><p>اختار مطعم من قائمة الديمو وهنوريك أكلاته.</p><Link className="button button-primary" to="/">الرجوع للمطاعم</Link></div>;

  const selectedMeal = restaurant.meals.find(meal => meal.id === selectedMealId);
  return <>
    <Link to="/" className="catalog-back-link"><ArrowRight size={17} aria-hidden="true" />كل المطاعم</Link>
    <section className="catalog-restaurant-intro" aria-labelledby="restaurant-heading">
      <div className="catalog-restaurant-copy"><span className="catalog-demo-label">مطعم ديمو</span><h1 id="restaurant-heading" tabIndex={-1}>{restaurant.name}</h1><span className="catalog-cuisine">{restaurant.cuisine}</span><p>{restaurant.description}</p><RestaurantFacts restaurant={restaurant} /></div>
      <div className={`catalog-restaurant-cover catalog-art-${restaurant.artwork}`}><FoodIllustration kind={restaurant.artwork} /></div>
    </section>
    <section className="catalog-menu" aria-labelledby="menu-heading">
      <div className="catalog-section-heading"><div><span className="catalog-section-kicker"><ChefHat size={16} aria-hidden="true" />من مطبخ {restaurant.name}</span><h2 id="menu-heading">قائمة الأكل</h2></div><span className="catalog-menu-total">{formatNumber(restaurant.meals.length)} أكلات</span></div>
      <div className="catalog-meal-grid">{restaurant.meals.map(meal => <MealCard key={meal.id} meal={meal} onSelect={setSelectedMealId} />)}</div>
      <p className="catalog-demo-caption">الأسماء والأسعار والتقييمات ووقت التوصيل بيانات تجريبية للعرض فقط.</p>
    </section>
    <MealDetails meal={selectedMeal} onClose={() => setSelectedMealId(null)} />
  </>;
}
