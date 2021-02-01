import React, { FunctionComponent } from "react";
import { Route, Switch } from "react-router-dom";
import BlacklistMovies from "./Movies";
import BlacklistSeries from "./Series";

const Router: FunctionComponent = () => {
  return (
    <Switch>
      <Route exact path="/blacklist/series">
        <BlacklistSeries></BlacklistSeries>
      </Route>
      <Route path="/blacklist/movies">
        <BlacklistMovies></BlacklistMovies>
      </Route>
    </Switch>
  );
};

export default Router;
