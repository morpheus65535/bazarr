import { useEffect, useState } from "react";
import { useEffectOnceWhen } from "rooks";

export async function waitFor(time: number) {
  return new Promise((resolved) => {
    setTimeout(resolved, time);
  });
}

export function useOnLoadedOnce(callback: () => void, entity: Async.Base<any>) {
  const [didLoaded, setLoaded] = useState(false);

  const { state } = entity;

  const isLoaded = state !== "loading";

  useEffect(() => {
    if (!isLoaded) {
      setLoaded(true);
    }
  }, [isLoaded]);

  useEffectOnceWhen(callback, didLoaded && isLoaded);
}
