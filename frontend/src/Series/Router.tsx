import React, { FunctionComponent } from "react";
import { Route, Switch } from "react-router-dom";
import Series from ".";
import { useItemUpdater, useSeries } from "../@redux/hooks";
import Episodes from "./Episodes";

interface Props {}

const Router: FunctionComponent<Props> = () => {
  const [, update] = useSeries();
  useItemUpdater(update);
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

export default Router;
