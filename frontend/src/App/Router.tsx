import React, { FunctionComponent, useMemo } from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import { useSystemSettings } from "../@redux/hooks";
import BlacklistRouter from "../Blacklist/Router";
import HistoryRouter from "../History/Router";
import MovieRouter from "../Movies/Router";
import SeriesRouter from "../Series/Router";
import SettingRouter from "../Settings/Router";
import SystemRouter from "../System/Router";
import WantedRouter from "../Wanted/Router";
import EmptyPage from "./404Page";

const Router: FunctionComponent<{ className?: string }> = ({ className }) => {
  const [settings] = useSystemSettings();
  const redirectPath = useMemo(() => {
    const general = settings.data?.general;
    const sonarr = general?.use_sonarr ?? false;
    const radarr = general?.use_radarr ?? false;
    if (sonarr) {
      return "/series";
    } else if (radarr) {
      return "/movies";
    } else {
      return "/settings";
    }
  }, [settings.data?.general]);
  return (
    <div className={className}>
      <Switch>
        <Route exact path="/">
          <Redirect exact to={redirectPath}></Redirect>
        </Route>
        <Route path="/series">
          <SeriesRouter></SeriesRouter>
        </Route>
        <Route path="/movies">
          <MovieRouter></MovieRouter>
        </Route>
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
        <Route path="*">
          <EmptyPage></EmptyPage>
        </Route>
      </Switch>
    </div>
  );
};

export default Router;
