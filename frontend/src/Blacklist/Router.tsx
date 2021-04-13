import React, { FunctionComponent } from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import { RouterEmptyPath } from "../404";
import {
  useIsRadarrEnabled,
  useIsSonarrEnabled,
  useSetSidebar,
} from "../@redux/hooks/site";
import BlacklistMovies from "./Movies";
import BlacklistSeries from "./Series";

const Router: FunctionComponent = () => {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();

  useSetSidebar("Blacklist");
  return (
    <Switch>
      {sonarr && (
        <Route exact path="/blacklist/series">
          <BlacklistSeries></BlacklistSeries>
        </Route>
      )}
      {radarr && (
        <Route path="/blacklist/movies">
          <BlacklistMovies></BlacklistMovies>
        </Route>
      )}
      <Route path="/blacklist/*">
        <Redirect to={RouterEmptyPath}></Redirect>
      </Route>
    </Switch>
  );
};

export default Router;
