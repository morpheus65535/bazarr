import { combineReducers } from "redux";
import badges from "./badges";
import movie from "./movie";
import series from "./series";
import site from "./site";
import system from "./system";

export default combineReducers({
  badges,
  system,
  series,
  movie,
  site,
});
