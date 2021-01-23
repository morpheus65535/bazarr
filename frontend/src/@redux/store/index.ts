import { createStore, applyMiddleware } from "redux";
import rootReducer from "../reducers";
import trunk from "redux-thunk";
import promise from "redux-promise";
import logger from "redux-logger";

let plugins = [promise, trunk];

if (process.env.NODE_ENV === "development") {
  plugins.push(logger);
}

let store = createStore(rootReducer, applyMiddleware(...plugins));
export default store;
