import React, { FunctionComponent } from "react";
import { Route, Switch } from "react-router-dom";

import Series from "./Series";
import Movies from "./Movies";

const Router: FunctionComponent = () => {
  return (
    <Switch>
      <Route exact path="/wanted/series">
        <Series></Series>
      </Route>
      <Route exact path="/wanted/movies">
        <Movies></Movies>
      </Route>
    </Switch>
  );
};

export default Router;
