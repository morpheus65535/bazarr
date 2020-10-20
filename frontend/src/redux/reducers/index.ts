import { combineReducers } from "redux";
import badges from "./badges";
import system from "./system";
import series from "./series"

export default combineReducers({
  badges,
  system,
  series
});
