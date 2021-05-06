import React, { FunctionComponent } from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import {
  useIsRadarrEnabled,
  useIsSonarrEnabled,
  useSetSidebar,
} from "../@redux/hooks/site";
import { RouterEmptyPath } from "../special-pages/404";
import Movies from "./Movies";
import Series from "./Series";

const Router: FunctionComponent = () => {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();

  useSetSidebar("Wanted");
  return (
    <Switch>
      {sonarr && (
        <Route exact path="/wanted/series">
          <Series></Series>
        </Route>
      )}
      {radarr && (
        <Route exact path="/wanted/movies">
          <Movies></Movies>
        </Route>
      )}
      <Route path="/wanted/*">
        <Redirect to={RouterEmptyPath}></Redirect>
      </Route>
    </Switch>
  );
};

export default Router;
