import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import type { Cart } from "../domain/models";
import { createUpdateQuantity } from "../application/update-quantity/use-case";
import { getErrorMessage } from "@/shared/domain/app-error";
interface MarketContext {
  carts: Cart[];
  favorites: string[];
  busy: boolean;
  issue: string;
  refresh(): Promise<void>;
  add(id: string, productId: string): Promise<void>;
  quantity(id: string, lineId: string, qty: number): Promise<void>;
  remove(id: string, lineId: string): Promise<void>;
  clear(id: string): Promise<void>;
  favorite(id: string): Promise<void>;
}
const Context = createContext<MarketContext | null>(null);
export function MarketplaceProvider({ children }: { children: ReactNode }) {
  const { marketplace: services } = useServices(),
    { user } = useSession();
  const owner = user?.id ?? null,
    latestOwner = useRef(owner);
  latestOwner.current = owner;
  const [snapshot, setSnapshot] = useState<{
    owner: string | null;
    carts: Cart[];
    favorites: string[];
  }>({ owner: null, carts: [], favorites: [] });
  const [busy, setBusy] = useState(false),
    [issue, setIssue] = useState("");
  const activeMutation = useRef(false);
  const refresh = useCallback(async () => {
    if (!owner) return;
    const [carts, favorites] = await Promise.all([
      services.carts.list(),
      services.catalog.favorites(),
    ]);
    if (latestOwner.current === owner) setSnapshot({ owner, carts, favorites });
  }, [owner, services]);
  useEffect(() => {
    setIssue("");
    const controller = new AbortController();
    if (owner)
      Promise.all([
        services.carts.list(controller.signal),
        services.catalog.favorites(controller.signal),
      ])
        .then(([carts, favorites]) => {
          if (!controller.signal.aborted && latestOwner.current === owner)
            setSnapshot({ owner, carts, favorites });
        })
        .catch((error) => {
          if (!controller.signal.aborted) setIssue(getErrorMessage(error));
        });
    return () => controller.abort();
  }, [owner, services]);
  async function change(action: () => Promise<Cart>) {
    if (activeMutation.current) return;
    activeMutation.current = true;
    setBusy(true);
    setIssue("");
    try {
      const cart = await action();
      if (latestOwner.current === owner)
        setSnapshot((previous) => ({
          owner,
          carts: [
            ...(previous.owner === owner ? previous.carts : []).filter(
              (c) => c.restaurantId !== cart.restaurantId,
            ),
            ...(cart.items.length ? [cart] : []),
          ],
          favorites: previous.owner === owner ? previous.favorites : [],
        }));
    } finally {
      activeMutation.current = false;
      setBusy(false);
    }
  }
  const visible: { carts: Cart[]; favorites: string[] } =
    snapshot.owner === owner ? snapshot : { carts: [], favorites: [] };
  return (
    <Context.Provider
      value={{
        ...visible,
        busy,
        issue,
        refresh,
        add: (id, productId) =>
          change(() => services.carts.add(id, productId, 1)),
        quantity: (id, lineId, qty) =>
          change(() => createUpdateQuantity(services.carts)(id, lineId, qty)),
        remove: (id, lineId) => change(() => services.carts.remove(id, lineId)),
        clear: (id) => change(() => services.carts.clear(id)),
        favorite: async (id) => {
          const values = await services.catalog.setFavorite(
            id,
            !visible.favorites.includes(id),
          );
          if (latestOwner.current === owner)
            setSnapshot((p) => ({
              carts: p.owner === owner ? p.carts : [],
              owner,
              favorites: values,
            }));
        },
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useMarketplace() {
  const value = useContext(Context);
  if (!value) throw new Error("MarketplaceProvider is required");
  return value;
}
