import { applyMiddleware, createStore } from "redux";
import logger from "redux-logger";
import promise from "redux-promise";
import trunk from "redux-thunk";
import rootReducer from "../reducers";

const plugins = [promise, trunk];

if (process.env.NODE_ENV === "development") {
  plugins.push(logger);
}

const store = createStore(rootReducer, applyMiddleware(...plugins));
export default store;
