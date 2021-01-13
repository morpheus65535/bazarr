import React from "react";
import { Route, Switch } from "react-router-dom";

import { connect } from "react-redux";
import { UpdateSystemSettings } from "../@redux/actions";

import General from "./General";
import Sonarr from "./Sonarr";
import Languages from "./Languages";
import Subtitles from "./Subtitles";

interface Props {
  update: () => void;
}

class Router extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/settings/general">
          <General></General>
        </Route>
        <Route exact path="/settings/sonarr">
          <Sonarr></Sonarr>
        </Route>
        <Route exact path="/settings/languages">
          <Languages></Languages>
        </Route>
        <Route exact path="/settings/subtitles">
          <Subtitles></Subtitles>
        </Route>
      </Switch>
    );
  }
}

export default connect(null, { update: UpdateSystemSettings })(Router);
