import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';

/** Keep one-time link data in memory while removing it through Router history. */
export function useSensitiveSearchParam(name: string): string {
  const [params, setParams] = useSearchParams();
  const incoming = params.get(name);
  const [value, setValue] = useState(incoming ?? '');

  useEffect(() => {
    if (incoming === null) return;
    setValue(incoming);
    setParams(current => {
      const next = new URLSearchParams(current);
      next.delete(name);
      return next;
    }, { replace: true });
  }, [incoming, name, setParams]);

  return value;
}
