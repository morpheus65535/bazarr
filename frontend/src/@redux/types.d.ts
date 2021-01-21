import { Action } from "redux-actions";
import { Dispatch } from "redux";

interface AsyncPayload<Payload> {
  loading: boolean;
  item?: Payload | string;
}

type AvaliableType = Action | ActionDispatcher;

type AsyncAction<Payload> = Action<AsyncPayload<Payload>>;
type ActionDispatcher = (dispatch: Dispatch<any>) => void;
type AsyncActionDispatcher<T> = (dispatch: Dispatch<AsyncAction<T>>) => void;
