import React, { FunctionComponent, useMemo } from "react";
import { Redirect, Route, Switch, useHistory } from "react-router-dom";
import { useDidMount } from "rooks";
import { useIsRadarrEnabled, useIsSonarrEnabled } from "../@redux/hooks/site";
import BlacklistRouter from "../Blacklist/Router";
import DisplayItemRouter from "../DisplayItem/Router";
import HistoryRouter from "../History/Router";
import SettingRouter from "../Settings/Router";
import EmptyPage, { RouterEmptyPath } from "../special-pages/404";
import SystemRouter from "../System/Router";
import { ScrollToTop } from "../utilities";
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

  const history = useHistory();

  useDidMount(() => {
    history.listen(() => {
      // This is a hack to make sure ScrollToTop will be triggered in the next frame (When everything are loaded)
      setTimeout(ScrollToTop);
    });
  });

  return (
    <div className={className}>
      <Switch>
        <Route exact path="/">
          <Redirect exact to={redirectPath}></Redirect>
        </Route>
        <Route path={["/series", "/movies"]}>
          <DisplayItemRouter></DisplayItemRouter>
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
