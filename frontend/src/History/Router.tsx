import React, { FunctionComponent } from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import { RouterEmptyPath } from "../404";
import { useIsRadarrEnabled, useIsSonarrEnabled } from "../@redux/hooks/site";
import MoviesHistory from "./Movies";
import SeriesHistory from "./Series";
import HistoryStats from "./Statistics";

const Router: FunctionComponent = () => {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();
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
