import React, { FunctionComponent } from "react";
import { Route, Switch } from "react-router-dom";
import MoviesHistory from "./Movies";
import SeriesHistory from "./Series";
import HistoryStats from "./Statistics";

const Router: FunctionComponent = () => {
  return (
    <Switch>
      <Route exact path="/history/series">
        <SeriesHistory></SeriesHistory>
      </Route>
      <Route path="/history/movies">
        <MoviesHistory></MoviesHistory>
      </Route>
      <Route path="/history/stats">
        <HistoryStats></HistoryStats>
      </Route>
    </Switch>
  );
};

export default Router;
