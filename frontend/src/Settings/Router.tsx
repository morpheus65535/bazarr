import React, { FunctionComponent, useEffect } from "react";
import { connect } from "react-redux";
import { Route, Switch } from "react-router-dom";
import { systemUpdateSettings } from "../@redux/actions";
import { LoadingIndicator } from "../components";
import General from "./General";
import Languages from "./Languages";
import Notifications from "./Notifications";
import Providers from "./Providers";
import Radarr from "./Radarr";
import Schedular from "./Schedular";
import Sonarr from "./Sonarr";
import Subtitles from "./Subtitles";

export const SettingsContext = React.createContext<SystemSettings | undefined>(
  undefined
);

interface Props {
  update: () => void;
  settings: AsyncState<SystemSettings | undefined>;
}

function mapStateToProps({ system }: StoreState) {
  return {
    settings: system.settings,
  };
}

const Router: FunctionComponent<Props> = ({ update, settings }) => {
  useEffect(() => update(), [update]);

  if (settings.updating && settings.items === undefined) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <SettingsContext.Provider value={settings.items}>
      <Switch>
        <Route exact path="/settings/general">
          <General></General>
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
    </SettingsContext.Provider>
  );
};

export default connect(mapStateToProps, { update: systemUpdateSettings })(
  Router
);
