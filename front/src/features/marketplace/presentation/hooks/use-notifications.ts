import { useCallback, useEffect, useState } from "react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import type { AppNotification } from "../../domain/models";

export function useNotifications(limit = 10) {
  const {
    marketplace: { notifications },
  } = useServices();
  const { user } = useSession();
  const userId = user?.id ?? "";
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState<{
    userId: string;
    items: AppNotification[];
    unreadCount: number;
    loading: boolean;
    error?: string;
  }>({
    userId: "",
    items: [],
    unreadCount: 0,
    loading: Boolean(userId),
  });

  useEffect(() => {
    if (!userId) {
      setState({ userId: "", items: [], unreadCount: 0, loading: false });
      return;
    }
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      if (controller.signal.aborted) return;
      if (document.visibilityState !== "hidden") {
        try {
          const page = await notifications.list(
            { limit, offset: 0 },
            controller.signal,
          );
          if (controller.signal.aborted) return;
          setState({
            userId,
            items: page.items,
            unreadCount: page.unreadCount,
            loading: false,
          });
        } catch (error) {
          if (!controller.signal.aborted) {
            setState((old) => ({
              userId,
              items: old.userId === userId ? old.items : [],
              unreadCount: old.userId === userId ? old.unreadCount : 0,
              loading: false,
              error: getErrorMessage(error),
            }));
          }
        }
      }
      if (!controller.signal.aborted) {
        timer = setTimeout(() => void poll(), 12000);
      }
    }

    void poll();
    return () => {
      controller.abort();
      if (timer) clearTimeout(timer);
    };
  }, [notifications, userId, limit, revision]);

  const refresh = useCallback(() => setRevision((v) => v + 1), []);

  const markRead = useCallback(
    async (notificationId: string) => {
      const updated = await notifications.markRead(notificationId);
      setState((old) => {
        if (old.userId !== userId) return old;
        let decremented = 0;
        const items = old.items.map((item) => {
          if (item.id !== notificationId) return item;
          if (!item.readAt && updated.readAt) decremented = 1;
          return updated;
        });
        return {
          ...old,
          items,
          unreadCount: Math.max(0, old.unreadCount - decremented),
        };
      });
    },
    [notifications, userId],
  );

  const markAllRead = useCallback(async () => {
    await notifications.markAllRead();
    const now = new Date().toISOString();
    setState((old) =>
      old.userId !== userId
        ? old
        : {
            ...old,
            unreadCount: 0,
            items: old.items.map((item) =>
              item.readAt ? item : { ...item, readAt: now },
            ),
          },
    );
  }, [notifications, userId]);

  const current = state.userId === userId ? state : undefined;
  return {
    items: current?.items ?? [],
    unreadCount: current?.unreadCount ?? 0,
    loading: Boolean(userId) && (current?.loading ?? true),
    error: current?.error,
    refresh,
    markRead,
    markAllRead,
  };
}
