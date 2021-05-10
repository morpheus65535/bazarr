import React, { FunctionComponent } from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import {
  useIsRadarrEnabled,
  useIsSonarrEnabled,
  useSetSidebar,
} from "../@redux/hooks/site";
import { RouterEmptyPath } from "../special-pages/404";
import MoviesHistory from "./Movies";
import SeriesHistory from "./Series";
import HistoryStats from "./Statistics";

const Router: FunctionComponent = () => {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();

  useSetSidebar("History");
  return (
    <Switch>
      {sonarr && (
        <Route exact path="/history/series">
          <SeriesHistory></SeriesHistory>
        </Route>
      )}
      {radarr && (
        <Route exact path="/history/movies">
          <MoviesHistory></MoviesHistory>
        </Route>
      )}
      <Route exact path="/history/stats">
        <HistoryStats></HistoryStats>
      </Route>
      <Route path="/history/*">
        <Redirect to={RouterEmptyPath}></Redirect>
      </Route>
    </Switch>
  );
};

export default Router;
