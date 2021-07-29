import { useCallback, useState } from "react";
import { useDidMount } from "rooks";

type RequestReturn<F extends () => Promise<any>> = PromiseType<ReturnType<F>>;

export function useAsyncRequest<F extends () => Promise<any>>(
  request: F,
  defaultData: RequestReturn<F>
): [AsyncState<RequestReturn<F>>, () => void] {
  const [state, setState] = useState<AsyncState<RequestReturn<F>>>({
    state: "idle",
    data: defaultData,
  });
  const update = useCallback(() => {
    setState((s) => ({ ...s, state: "loading" }));
    request()
      .then((res) => setState({ state: "succeeded", data: res }))
      .catch((err) => setState((s) => ({ ...s, state: "failed", err })));
  }, [request]);

  useDidMount(update);

  return [state, update];
}
