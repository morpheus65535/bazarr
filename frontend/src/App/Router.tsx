import React, { FunctionComponent, useMemo } from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import EmptyPage, { RouterEmptyPath } from "../404";
import { useIsRadarrEnabled, useIsSonarrEnabled } from "../@redux/hooks/site";
import BlacklistRouter from "../Blacklist/Router";
import HistoryRouter from "../History/Router";
import MovieRouter from "../Movies/Router";
import SeriesRouter from "../Series/Router";
import SettingRouter from "../Settings/Router";
import SystemRouter from "../System/Router";
import { ScrollToTop } from "../utilites";
import WantedRouter from "../Wanted/Router";

const Router: FunctionComponent<{ className?: string }> = ({ className }) => {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();
  const redirectPath = useMemo(() => {
    if (sonarr) {
      return "/series";
    } else if (radarr) {
      return "/movies";
    } else {
      return "/settings";
    }
  }, [sonarr, radarr]);
  return (
    <div className={className}>
      <ScrollToTop />
      <Switch>
        <Route exact path="/">
          <Redirect exact to={redirectPath}></Redirect>
        </Route>
        {sonarr && (
          <Route path="/series">
            <SeriesRouter></SeriesRouter>
          </Route>
        )}
        {radarr && (
          <Route path="/movies">
            <MovieRouter></MovieRouter>
          </Route>
        )}
        <Route path="/wanted">
          <WantedRouter></WantedRouter>
        </Route>
        <Route path="/history">
          <HistoryRouter></HistoryRouter>
        </Route>
        <Route path="/blacklist">
          <BlacklistRouter></BlacklistRouter>
        </Route>
        <Route path="/settings">
          <SettingRouter></SettingRouter>
        </Route>
        <Route path="/system">
          <SystemRouter></SystemRouter>
        </Route>
        <Route exact path={RouterEmptyPath}>
          <EmptyPage></EmptyPage>
        </Route>
        <Route path="*">
          <Redirect to={RouterEmptyPath}></Redirect>
        </Route>
      </Switch>
    </div>
  );
};

export default Router;
