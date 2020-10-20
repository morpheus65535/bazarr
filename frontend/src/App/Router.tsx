import React from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import { connect } from "react-redux";

import Series from "../Series";
import SystemRouter from "../System/Router"

class Router extends React.Component {
  render(): JSX.Element {
    return (
      <div className="d-flex flex-row">
        <Switch>
          <Route exact path="/">
            <Redirect exact to="/series"></Redirect>
          </Route>
          <Route exact path="/series">
            <Series />
          </Route>
          <Route path="/settings">
            <span>Settings</span>
          </Route>
          <Route path="/system">
            <SystemRouter></SystemRouter>
          </Route>
        </Switch>
      </div>
    );
  }
}

export default connect()(Router);
