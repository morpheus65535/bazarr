import { combineReducers } from "redux";
import badges from "./badges";
import system from "./system";
import series from "./series";
import movie from "./movie";

export default combineReducers({
  badges,
  system,
  series,
  movie,
});
