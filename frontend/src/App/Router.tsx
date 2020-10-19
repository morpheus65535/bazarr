import React from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import { connect } from "react-redux";

import Series from "../Series";

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
          <Route exact path="/settings">
            <span>Settings</span>
          </Route>
        </Switch>
      </div>
    );
  }
}

export default connect()(Router);
