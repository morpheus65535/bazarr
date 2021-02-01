import React, { FunctionComponent, useEffect } from "react";
import { connect } from "react-redux";
import { Route, Switch } from "react-router-dom";
import Series from ".";
import { seriesUpdateList } from "../@redux/actions";
import Episodes from "./Episodes";

interface Props {
  update: () => void;
}

const Router: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);
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
};

export default connect(null, { update: seriesUpdateList })(Router);
