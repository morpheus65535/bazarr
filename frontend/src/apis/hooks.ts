import { useCallback, useState } from "react";

type Request = (...args: any[]) => Promise<any>;
type Return<T extends Request> = PromiseType<ReturnType<T>>;

export function useAsyncRequest<F extends Request>(
  request: F,
  initial: Return<F>
): [Async.Base<Return<F>>, (...args: Parameters<F>) => void] {
  const [state, setState] = useState<Async.Base<Return<F>>>({
    state: "uninitialized",
    content: initial,
    error: null,
  });
  const update = useCallback(
    (...args: Parameters<F>) => {
      setState((s) => ({ ...s, state: "loading" }));
      request(...args)
        .then((res) =>
          setState({ state: "succeeded", content: res, error: null })
        )
        .catch((error) => setState((s) => ({ ...s, state: "failed", error })));
    },
    [request]
  );

  return [state, update];
}
