import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import type { Cart } from "../domain/models";
import { createUpdateQuantity } from "../application/update-quantity/use-case";
import { AppError, getErrorMessage } from "@/shared/domain/app-error";
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
interface MarketSession {
  owner: string | null;
  cartRevision: number;
  favoriteRevision: number;
  cartRead: number;
  favoriteRead: number;
  cartPending: boolean;
  favorites: string[];
  favoriteQueue: Promise<void>;
}
export function MarketplaceProvider({ children }: { children: ReactNode }) {
  const { marketplace: services } = useServices(),
    { user } = useSession();
  const owner = user?.id ?? null;
  const session = useMemo<MarketSession>(() => ({
    owner,
    cartRevision: 0,
    favoriteRevision: 0,
    cartRead: 0,
    favoriteRead: 0,
    cartPending: false,
    favorites: [],
    favoriteQueue: Promise.resolve(),
  }), [owner]);
  const latestSession = useRef(session);
  latestSession.current = session;
  const [snapshot, setSnapshot] = useState<{
    session: MarketSession;
    carts: Cart[];
    favorites: string[];
  }>({ session, carts: [], favorites: [] });
  const [busySession, setBusySession] = useState<MarketSession | null>(null),
    [issue, setIssue] = useState<{ session: MarketSession; message: string } | null>(null);
  const loadSnapshot = useCallback(async (signal?: AbortSignal) => {
    if (!session.owner || latestSession.current !== session) return;
    const cartRead = ++session.cartRead;
    const favoriteRead = ++session.favoriteRead;
    const current = () => latestSession.current === session && !signal?.aborted;
    // If a mutation finishes during a read, read again instead of publishing
    // an older snapshot over that mutation's confirmed response.
    async function loadCarts() {
      while (current() && cartRead === session.cartRead) {
        const revision = session.cartRevision;
        const carts = await services.carts.list(signal);
        if (!current() || cartRead !== session.cartRead) return;
        if (revision !== session.cartRevision) continue;
        setSnapshot((previous) => ({
          session,
          carts,
          favorites: previous.session === session ? previous.favorites : [],
        }));
        return;
      }
    }
    async function loadFavorites() {
      while (current() && favoriteRead === session.favoriteRead) {
        const revision = session.favoriteRevision;
        const favorites = await services.catalog.favorites(signal);
        if (!current() || favoriteRead !== session.favoriteRead) return;
        if (revision !== session.favoriteRevision) continue;
        session.favorites = favorites;
        setSnapshot((previous) => ({
          session,
          carts: previous.session === session ? previous.carts : [],
          favorites,
        }));
        return;
      }
    }
    await Promise.all([loadCarts(), loadFavorites()]);
  }, [services, session]);
  const refresh = useCallback(async () => {
    const request = loadSnapshot();
    const read = session.cartRead;
    await request;
    if (latestSession.current === session && read === session.cartRead) setIssue(null);
  }, [loadSnapshot, session]);
  useEffect(() => {
    const controller = new AbortController();
    const request = loadSnapshot(controller.signal);
    const read = session.cartRead;
    void request.catch((error) => {
      if (!controller.signal.aborted && latestSession.current === session && read === session.cartRead)
        setIssue({ session, message: getErrorMessage(error) });
    });
    return () => controller.abort();
  }, [loadSnapshot, session]);
  async function change(action: () => Promise<Cart>) {
    if (!session.owner || latestSession.current !== session)
      throw new AppError("authentication_required", "سجّل الدخول عشان تكمل.");
    if (session.cartPending)
      throw new AppError("cart_update_pending", "استنى تحديث السلة الحالي وبعدين جرّب تاني.");
    session.cartPending = true;
    setBusySession(session);
    setIssue(null);
    try {
      const cart = await action();
      if (latestSession.current === session) {
        session.cartRevision += 1;
        setSnapshot((previous) => ({
          session,
          carts: [
            ...(previous.session === session ? previous.carts : []).filter(
              (c) => c.restaurantId !== cart.restaurantId,
            ),
            ...(cart.items.length ? [cart] : []),
          ],
          favorites: previous.session === session ? previous.favorites : [],
        }));
      }
    } finally {
      session.cartPending = false;
      setBusySession((previous) => previous === session ? null : previous);
    }
  }
  const visible: { carts: Cart[]; favorites: string[] } =
    snapshot.session === session ? snapshot : { carts: [], favorites: [] };
  return (
    <Context.Provider
      value={{
        ...visible,
        busy: busySession === session,
        issue: issue?.session === session ? issue.message : "",
        refresh,
        add: (id, productId) =>
          change(() => services.carts.add(id, productId, 1)),
        quantity: (id, lineId, qty) =>
          change(() => createUpdateQuantity(services.carts)(id, lineId, qty)),
        remove: (id, lineId) => change(() => services.carts.remove(id, lineId)),
        clear: (id) => change(() => services.carts.clear(id)),
        favorite: (id) => {
          const request = session.favoriteQueue.then(async () => {
            if (!session.owner || latestSession.current !== session)
              throw new AppError("authentication_required", "سجّل الدخول عشان تكمل.");
            const favorites = await services.catalog.setFavorite(
              id,
              !session.favorites.includes(id),
            );
            if (latestSession.current === session) {
              session.favoriteRevision += 1;
              session.favorites = favorites;
              setSnapshot((previous) => ({
                session,
                carts: previous.session === session ? previous.carts : [],
                favorites,
              }));
            }
          });
          session.favoriteQueue = request.catch(() => undefined);
          return request;
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
