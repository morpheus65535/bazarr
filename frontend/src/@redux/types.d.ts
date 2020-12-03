import { Action } from "redux-actions";

interface AsyncPayload<Payload> {
  loading: boolean;
  item?: Payload | string;
}

type AsyncAction<Payload> = Action<AsyncPayload<Payload>>;
