import { useState } from "react";
import { Store } from "lucide-react";

function isAllowedLogoSource(value: string): boolean {
  if (/^\/images\/marketplace\/[\w.-]+\.(svg|png|webp)$/i.test(value)) return true;
  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" &&
      ["talabat.dhmedia.io", "images.deliveryhero.io"].includes(url.hostname)
    );
  } catch {
    return false;
  }
}

export function MerchantLogo({
  logo,
  name,
}: {
  logo: string | null;
  name: string;
}) {
  const source = logo && isAllowedLogoSource(logo) ? logo : undefined;
  const [failedSource, setFailedSource] = useState<string | null>(null);
  return (
    <span className="mp-merchant-logo">
      {source && failedSource !== source ? (
        <img
          src={source}
          alt={name}
          width="54"
          height="54"
          loading="lazy"
          onError={() => setFailedSource(source)}
        />
      ) : (
        <Store size={25} aria-hidden="true" />
      )}
    </span>
  );
}
