import React, { FunctionComponent } from "react";
import { Redirect, Route, Switch } from "react-router-dom";
import { connect } from "react-redux";

import SeriesRouter from "../Series/Router";
import MovieRouter from "../Movies/Router";
import SystemRouter from "../System/Router";
import SettingRouter from "../Settings/Router";
import WantedRouter from "../Wanted/Router";
import HistoryRouter from "../History/Router";
import BlacklistRouter from "../Blacklist/Router";

const Router: FunctionComponent<{ className?: string }> = ({ className }) => {
  return (
    <div className={className}>
      <Switch>
        <Route exact path="/">
          <Redirect exact to="/series"></Redirect>
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
      </Switch>
    </div>
  );
};

export default connect()(Router);
