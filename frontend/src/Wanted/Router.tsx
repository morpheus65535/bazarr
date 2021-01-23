import React from "react";
import { Route, Switch } from "react-router-dom";

import Series from "./Series";
import Movies from "./Movies";

class Router extends React.Component {
  render(): JSX.Element {
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
  }
}

export default Router;
