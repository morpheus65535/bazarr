import React from "react";
import { Route, Switch } from "react-router-dom";

import { connect } from "react-redux";
import { updateSeriesList } from "../redux/actions/series";

import Series from ".";
import Episodes from "./Episodes";

interface Props {
  updateSeriesList: () => void;
}

class Router extends React.Component<Props> {
  componentDidMount() {
    this.props.updateSeriesList();
  }
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/series">
          <Series></Series>
        </Route>
        <Route path="/series/:id">
          <Episodes></Episodes>
        </Route>
      </Switch>
    );
  }
}

export default connect(null, { updateSeriesList })(Router);
