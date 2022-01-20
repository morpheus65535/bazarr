import { useCallback, useRef, useState } from "react";

type Request = (...args: any[]) => Promise<any>;
type Return<T extends Request> = PromiseType<ReturnType<T>>;

export function useAsyncRequest<F extends Request>(
  request: F
): [Async.Item<Return<F>>, (...args: Parameters<F>) => void] {
  const [state, setState] = useState<Async.Item<Return<F>>>({
    state: "uninitialized",
    content: null,
    error: null,
  });

  const requestRef = useRef(request);

  const update = useCallback(
    (...args: Parameters<F>) => {
      setState((s) => ({ ...s, state: "loading" }));
      requestRef
        .current(...args)
        .then((res) =>
          setState({ state: "succeeded", content: res, error: null })
        )
        .catch((error) => setState((s) => ({ ...s, state: "failed", error })));
    },
    [requestRef]
  );

  return [state, update];
}

export * from "./badges";
export * from "./system";
