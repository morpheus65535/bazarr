import React from "react";
import { Redirect, Route, Switch } from "react-router-dom";

import Status from "./Status";

class Router extends React.Component {
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/system">
          <Redirect exact to="/series"></Redirect>
        </Route>
        <Route exact path="/system/status">
          <Status></Status>
        </Route>
      </Switch>
    );
  }
}

export default Router;
