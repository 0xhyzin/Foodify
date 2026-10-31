import { useEffect, useState } from "react";
import { getErrorMessage } from "@/shared/domain/app-error";
export function useResource<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState<{
    load: typeof load;
    revision: number;
    data?: T;
    error?: string;
  }>();
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setState({ load, revision, data });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setState({ load, revision, error: getErrorMessage(error) });
      });
    return () => controller.abort();
  }, [load, revision]);
  const current =
    state?.load === load && state.revision === revision ? state : undefined;
  return {
    data: current?.data,
    error: current?.error,
    loading: !current,
    reload: () => setRevision((v) => v + 1),
  };
}
