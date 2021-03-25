import { combineReducers } from "redux";
import movie from "./movie";
import series from "./series";
import site from "./site";
import system from "./system";

export default combineReducers({
  system,
  series,
  movie,
  site,
});
