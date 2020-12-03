import React from "react";
import { Route, Switch } from "react-router-dom";

import { connect } from "react-redux";

import SeriesHistory from "./series";
import MoviesHistory from "./movies";

class Router extends React.Component {
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/history/series">
          <SeriesHistory></SeriesHistory>
        </Route>
        <Route path="/history/movies">
          <MoviesHistory></MoviesHistory>
        </Route>
      </Switch>
    );
  }
}

export default connect(null)(Router);
