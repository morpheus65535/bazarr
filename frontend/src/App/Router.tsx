import React from "react";
import { Redirect, Route, Switch } from "react-router-dom";

class Router extends React.Component {
  render(): JSX.Element {
    return (
      <div className="d-flex flex-row">
        <Switch>
          <Route exact path="/">
            <Redirect exact to="/series"></Redirect>
          </Route>
          <Route exact path="/series">
            <span>Series</span>
          </Route>
          <Route exact path="/settings">
            <span>Settings</span>
          </Route>
        </Switch>
      </div>
    );
  }
}

export default Router;
