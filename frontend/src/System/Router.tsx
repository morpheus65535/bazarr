import React, { FunctionComponent } from "react";
import { Route, Switch } from "react-router-dom";
import Logs from "./Logs";
import Providers from "./Providers";
import Releases from "./Releases";
import Status from "./Status";
import Tasks from "./Tasks";

const Router: FunctionComponent = () => {
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
      <Route exact path="/system/releases">
        <Releases></Releases>
      </Route>
    </Switch>
  );
};

export default Router;
