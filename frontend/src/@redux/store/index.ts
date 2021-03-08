import { applyMiddleware, createStore } from "redux";
import logger from "redux-logger";
import promise from "redux-promise";
import trunk from "redux-thunk";
import rootReducer from "../reducers";

const plugins = [promise, trunk];

if (
  process.env.NODE_ENV === "development" &&
  process.env["REACT_APP_LOG_REDUX_EVENT"] !== "false"
) {
  plugins.push(logger);
}

const store = createStore(rootReducer, applyMiddleware(...plugins));
export default store;
