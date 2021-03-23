import { Dispatch } from "redux";
import { Action } from "redux-actions";

interface AsyncPayload<Payload> {
  loading: boolean;
  item?: Payload | Error;
  parameters: any[];
}

type AvailableType<T> = Action<T> | ActionDispatcher<T>;

type AsyncAction<Payload> = Action<AsyncPayload<Payload>>;
type ActionDispatcher<T = any> = (dispatch: Dispatch<Action<T>>) => void;
type AsyncActionDispatcher<T> = (
  dispatch: Dispatch<AsyncAction<T>>
) => Promise<void>;

type PromiseCreator = (...args: any[]) => Promise<any>;
type AvailableCreator = (...args: any[]) => AvailableType<any>[];
type AsyncActionCreator = (...args: any[]) => AsyncActionDispatcher<any>[];

type ActionCallback = () => Action<any> | void;
