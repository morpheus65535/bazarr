import React, { FunctionComponent } from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import { useIsRadarrEnabled, useIsSonarrEnabled } from "../@redux/hooks";
import { RouterEmptyPath } from "../special-pages/404";
import Episodes from "./Episodes";
import MovieDetail from "./MovieDetail";
import Movies from "./Movies";
import Series from "./Series";

interface Props {}

const Router: FunctionComponent<Props> = () => {
  const radarr = useIsRadarrEnabled();
  const sonarr = useIsSonarrEnabled();

  return (
    <Switch>
      {radarr && (
        <Route exact path="/movies">
          <Movies></Movies>
        </Route>
      )}
      {radarr && (
        <Route path="/movies/:id">
          <MovieDetail></MovieDetail>
        </Route>
      )}
      {sonarr && (
        <Route exact path="/series">
          <Series></Series>
        </Route>
      )}
      {sonarr && (
        <Route path="/series/:id">
          <Episodes></Episodes>
        </Route>
      )}
      <Route path="*">
        <Redirect to={RouterEmptyPath}></Redirect>
      </Route>
    </Switch>
  );
};

export default Router;
