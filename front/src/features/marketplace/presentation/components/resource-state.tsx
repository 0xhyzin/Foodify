import { ShoppingBag } from "lucide-react";
import { Button } from "@/shared/ui/button";
export function ResourceState({
  loading,
  error,
  retry,
}: {
  loading?: boolean;
  error?: string;
  retry?: () => void;
}) {
  return (
    <div className="mp-resource" role={error ? "alert" : "status"}>
      {loading ? (
        <>
          <span className="mp-loading" />
          بنجهّز اختياراتك…
        </>
      ) : (
        <>
          <ShoppingBag aria-hidden="true" size={34} />
          <p>{error ?? "مفيش نتائج للاختيارات دي."}</p>
          {retry ? (
            <Button variant="secondary" onClick={retry}>
              حاول تاني
            </Button>
          ) : null}
        </>
      )}
    </div>
  );
}
