import { useRef } from 'react';
import { Beef, LayoutGrid, Pizza, Sandwich, Search, UtensilsCrossed, X, type LucideIcon } from 'lucide-react';
import type { CatalogCategory } from '../../domain/models';

const categoryIcons: Record<CatalogCategory, LucideIcon> = { all: LayoutGrid, burger: Beef, pizza: Pizza, bowl: UtensilsCrossed, wrap: Sandwich };

interface CatalogFiltersProps {
  categories: ReadonlyArray<{ id: CatalogCategory; label: string }>;
  category: CatalogCategory;
  query: string;
  onCategoryChange(category: CatalogCategory): void;
  onQueryChange(query: string): void;
}

export function CatalogFilters({ categories, category, query, onCategoryChange, onQueryChange }: CatalogFiltersProps) {
  const searchInput = useRef<HTMLInputElement>(null);
  return <div className="catalog-filters">
    <div className="catalog-search">
      <label htmlFor="restaurant-search" className="catalog-search-label">بتدور على إيه؟</label>
      <div className="catalog-search-control">
        <Search size={21} aria-hidden="true" />
        <input ref={searchInput} id="restaurant-search" type="search" value={query} placeholder="دور على مطعم أو أكلة بتحبها…" onChange={event => onQueryChange(event.target.value)} autoComplete="off" aria-controls="restaurants-list" />
        {query && <button type="button" onClick={() => { onQueryChange(''); searchInput.current?.focus(); }} aria-label="مسح البحث"><X size={19} /></button>}
      </div>
    </div>
    <div className="catalog-categories" role="group" aria-label="نوع الأكل">
      {categories.map(item => {
        const Icon = categoryIcons[item.id];
        return <button key={item.id} type="button" className="catalog-category" aria-pressed={category === item.id} onClick={() => onCategoryChange(item.id)}><Icon size={18} aria-hidden="true" />{item.label}</button>;
      })}
    </div>
  </div>;
}
