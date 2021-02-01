import React, { FunctionComponent } from "react";
import { Route, Switch } from "react-router-dom";
import MoviesHistory from "./Movies";
import SeriesHistory from "./Series";

const Router: FunctionComponent = () => {
  return (
    <Switch>
      <Route exact path="/history/series">
        <SeriesHistory></SeriesHistory>
      </Route>
      <Route path="/history/movies">
        <MoviesHistory></MoviesHistory>
      </Route>
    </Switch>
  );
};

export default Router;
