import React from "react";
import { Route, Switch } from "react-router-dom";

import General from "./General";
import Languages from "./Languages";

class Router extends React.Component {
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/settings/general">
          <General></General>
        </Route>
        <Route exact path="/settings/languages">
          <Languages></Languages>
        </Route>
      </Switch>
    );
  }
}

export default Router;
