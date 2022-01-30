import { combineReducers } from "@reduxjs/toolkit";
import modalReducer from "./modal";
import siteReducer from "./site";

const reducers = combineReducers({
  site: siteReducer,
  modal: modalReducer,
});

export default reducers;
