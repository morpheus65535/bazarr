import React from "react";
import { Route, Switch } from "react-router-dom";

import { connect } from "react-redux";
import { UpdateSystemSettings } from "../@redux/actions";

import Status from "./Status";
import Tasks from "./Tasks";
import Providers from "./Providers";
import Logs from "./Logs";

interface Props {
  update: () => void;
}

class Router extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/system/tasks">
          <Tasks></Tasks>
        </Route>
        <Route exact path="/system/status">
          <Status></Status>
        </Route>
        <Route exact path="/system/providers">
          <Providers></Providers>
        </Route>
        <Route exact path="/system/logs">
          <Logs></Logs>
        </Route>
      </Switch>
    );
  }
}

export default connect(null, { update: UpdateSystemSettings })(Router);
