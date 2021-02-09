import { Dispatch } from "redux";
import { Action } from "redux-actions";

interface AsyncPayload<Payload> {
  loading: boolean;
  item?: Payload | Error;
}

type AvaliableType = Action | ActionDispatcher;

type AsyncAction<Payload> = Action<AsyncPayload<Payload>>;
type ActionDispatcher<T = any> = (dispatch: Dispatch<Action<T>>) => void;
type AsyncActionDispatcher<T> = (dispatch: Dispatch<AsyncAction<T>>) => void;

type FillfulActionDispatcher = (state: StoreState) => Action<any> | undefined;
