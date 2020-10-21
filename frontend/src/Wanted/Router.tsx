import React from "react";
import { Route, Switch } from "react-router-dom";

import Series from "./Series";

class Router extends React.Component {
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/wanted/series">
          <Series></Series>
        </Route>
      </Switch>
    );
  }
}

export default Router;
