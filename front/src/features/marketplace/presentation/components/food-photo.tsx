import { useState } from "react";
import {
  Apple,
  Beef,
  CakeSlice,
  Coffee,
  CupSoda,
  Flame,
  ImageOff,
  Milk,
  Package,
  Pizza,
  Sandwich,
  Soup,
  SprayCan,
  UtensilsCrossed,
  Wheat,
} from "lucide-react";

const categoryIcons = {
  burger: Beef,
  pizza: Pizza,
  chicken: UtensilsCrossed,
  shawarma: Sandwich,
  wrap: Sandwich,
  egyptian: Soup,
  bowl: Soup,
  grill: Flame,
  cake: CakeSlice,
  oriental: CakeSlice,
  bakery: Wheat,
  donut: CakeSlice,
  donuts: CakeSlice,
  coffee: Coffee,
  grocery: Package,
  basics: Package,
  dairy: Milk,
  produce: Apple,
  drinks: CupSoda,
  household: SprayCan,
};

export function FoodPhoto({
  kind,
  className = "",
}: {
  kind: string;
  className?: string;
}) {
  const source = getSafeImageUrl(kind);
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const category = kind.toLowerCase();
  const Icon = categoryIcons[category as keyof typeof categoryIcons] ?? ImageOff;

  if (source && failedSource !== source) {
    return (
      <div
        className={`mp-photo mp-food-image${isPackagedProductPhoto(source) ? " mp-product-pack" : ""} ${className}`}
        aria-hidden="true"
      >
        <img
          src={source}
          alt=""
          loading="lazy"
          decoding="async"
          onError={() => setFailedSource(source)}
        />
      </div>
    );
  }

  return (
    <div className={`mp-photo mp-food-icon ${className}`} aria-hidden="true">
      <Icon strokeWidth={1.4} />
    </div>
  );
}

function getSafeImageUrl(value: string): string | undefined {
  try {
    const url = new URL(value);
    if (
      url.protocol === "https:" &&
      ["talabat.dhmedia.io", "images.deliveryhero.io"].includes(url.hostname)
    ) {
      return url.href;
    }
  } catch {
    /* A category key or invalid URL falls back to its icon. */
  }
  return undefined;
}

function isPackagedProductPhoto(source: string): boolean {
  return source.includes("/product-information-management/") || source.includes("/darkstores/");
}
