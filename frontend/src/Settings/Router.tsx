import React, { FunctionComponent, useEffect } from "react";
import { connect } from "react-redux";
import { Route, Switch } from "react-router-dom";
import { systemUpdateSettings } from "../@redux/actions";
import General from "./General";
import Languages from "./Languages";
import Notifications from "./Notifications";
import Providers from "./Providers";
import Radarr from "./Radarr";
import Schedular from "./Schedular";
import Sonarr from "./Sonarr";
import Subtitles from "./Subtitles";
import UI from "./UI";

interface Props {
  update: () => void;
}

const Router: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);

  return (
    <Switch>
      <Route exact path="/settings/general">
        <General></General>
      </Route>
      <Route exact path="/settings/ui">
        <UI></UI>
      </Route>
      <Route exact path="/settings/sonarr">
        <Sonarr></Sonarr>
      </Route>
      <Route exact path="/settings/radarr">
        <Radarr></Radarr>
      </Route>
      <Route exact path="/settings/languages">
        <Languages></Languages>
      </Route>
      <Route exact path="/settings/subtitles">
        <Subtitles></Subtitles>
      </Route>
      <Route exact path="/settings/schedular">
        <Schedular></Schedular>
      </Route>
      <Route exact path="/settings/providers">
        <Providers></Providers>
      </Route>
      <Route exact path="/settings/notifications">
        <Notifications></Notifications>
      </Route>
    </Switch>
  );
};

export default connect(undefined, { update: systemUpdateSettings })(Router);
