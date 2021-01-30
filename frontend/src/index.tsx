import React, { FunctionComponent, useMemo } from "react";
import ReactDOM from "react-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import App from "./App";
import Auth from "./Auth";
import { Switch, Route, Redirect } from "react-router";
import { BrowserRouter } from "react-router-dom";
import { Provider, useSelector } from "react-redux";
import store from "./@redux/store";

import "./@scss/index.scss";

const loginUrl = "/login";

const Entrance: FunctionComponent = () => {
  const baseUrl = useMemo(
    () => (process.env.NODE_ENV === "production" ? window.Bazarr.baseUrl : "/"),
    []
  );

  const auth = useSelector<StoreState, boolean>((s) => s.site.auth);

  const app = useMemo(
    () => (auth ? <App></App> : <Redirect to={loginUrl}></Redirect>),
    [auth]
  );

  return (
    <BrowserRouter basename={baseUrl}>
      <Switch>
        <Route exact path={loginUrl}>
          <Auth></Auth>
        </Route>
        <Route path="/">{app}</Route>
      </Switch>
    </BrowserRouter>
  );
};

ReactDOM.render(
  <Provider store={store}>
    {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
    {/* <React.StrictMode> */}
    <Entrance></Entrance>
    {/* </React.StrictMode> */}
  </Provider>,
  document.getElementById("root")
);
