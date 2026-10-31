import { Info } from "lucide-react";

export function CatalogSampleNote() {
  return (
    <aside className="mp-demo-note" role="note">
      <Info aria-hidden="true" size={17} />
      <p>
        بيانات المتاجر والمنتجات محفوظة في قاعدة البيانات. الأسعار والتقييمات ووقت
        التوصيل أمثلة للعرض وليست تحديثًا مباشرًا من المتاجر.
      </p>
    </aside>
  );
}
