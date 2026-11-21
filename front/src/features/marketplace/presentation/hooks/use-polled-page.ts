import { useCallback, useEffect, useRef, useState } from "react";
import { getErrorMessage } from "@/shared/domain/app-error";

export function usePolledPage<T>(
  enabled: boolean,
  queryKey: string,
  loader: (signal: AbortSignal) => Promise<T>,
  intervalMs = 10000,
) {
  const loaderRef = useRef(loader);
  loaderRef.current = loader;
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState<{
    key: string;
    data?: T;
    error?: string;
  }>({ key: "" });

  useEffect(() => {
    if (!enabled) {
      setState({ key: queryKey });
      return;
    }
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      if (controller.signal.aborted) return;
      if (document.visibilityState !== "hidden") {
        try {
          const data = await loaderRef.current(controller.signal);
          if (!controller.signal.aborted) {
            setState({ key: queryKey, data });
          }
        } catch (cause) {
          if (!controller.signal.aborted) {
            setState((old) => ({
              key: queryKey,
              data: old.key === queryKey ? old.data : undefined,
              error: getErrorMessage(cause),
            }));
          }
        }
      }
      if (!controller.signal.aborted) {
        timer = setTimeout(() => void poll(), intervalMs);
      }
    }

    void poll();
    return () => {
      controller.abort();
      if (timer) clearTimeout(timer);
    };
  }, [enabled, queryKey, revision, intervalMs]);

  const reload = useCallback(() => setRevision((v) => v + 1), []);
  const current = state.key === queryKey ? state : undefined;

  return {
    data: current?.data,
    error: current?.error,
    loading: enabled && current === undefined,
    reload,
  };
}
