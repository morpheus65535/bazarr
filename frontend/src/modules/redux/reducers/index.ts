import { combineReducers } from "@reduxjs/toolkit";
import siteReducer from "./site";

const reducers = combineReducers({
  site: siteReducer,
});

export default reducers;
