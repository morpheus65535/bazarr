import { AsyncAction } from "../types/actions";

export function mapToAsyncState<Payload>(
  action: AsyncAction<Payload>,
  defVal: Payload
): AsyncState<Payload> {
  if (action.payload.loading) {
    return {
      loading: true,
      lastResult: undefined,
      items: defVal,
    };
  } else if (action.error !== undefined) {
    return {
      loading: false,
      lastResult: action.payload.item as string,
      items: defVal,
    };
  } else {
    return {
      loading: false,
      lastResult: undefined,
      items: action.payload.item as Payload,
    };
  }
}
