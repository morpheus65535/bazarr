import React from "react";
import { Route, Switch } from "react-router-dom";

import Status from "./Status";
import Tasks from "./Tasks";

class Router extends React.Component {
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/system/tasks">
          <Tasks></Tasks>
        </Route>
        <Route exact path="/system/status">
          <Status></Status>
        </Route>
      </Switch>
    );
  }
}

export default Router;
