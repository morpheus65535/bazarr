import { Action } from "redux-actions";

export interface AsyncPayload<Payload> {
  loading: boolean;
  item?: Payload | string;
}

export type AsyncAction<Payload> = Action<AsyncPayload<Payload>>;

