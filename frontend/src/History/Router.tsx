import React, { FunctionComponent } from "react";
import { Route, Switch } from "react-router-dom";

import SeriesHistory from "./Series";
import MoviesHistory from "./Movies";

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
