import { useCallback, useState } from "react";
import { useDidMount } from "rooks";

type RequestReturn<F extends () => Promise<any>> = PromiseType<ReturnType<F>>;

export function useAsyncRequest<F extends () => Promise<any>>(
  request: F,
  defaultData: RequestReturn<F>
): [AsyncState<RequestReturn<F>>, () => void] {
  const [state, setState] = useState<AsyncState<RequestReturn<F>>>({
    updating: true,
    data: defaultData,
  });
  const update = useCallback(() => {
    setState((s) => ({ ...s, updating: true }));
    request()
      .then((res) => setState({ updating: false, data: res }))
      .catch((err) => setState((s) => ({ ...s, updating: false, err })));
  }, [request]);

  useDidMount(update);

  return [state, update];
}
