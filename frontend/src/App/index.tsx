import React, { FunctionComponent, useEffect } from "react";
import { Row } from "react-bootstrap";
import { Provider } from "react-redux";
import { Route, Switch } from "react-router";
import { BrowserRouter, Redirect } from "react-router-dom";
import { useEffectOnceWhen } from "rooks";
import Socketio from "../@modules/socketio";
import { useReduxStore } from "../@redux/hooks/base";
import { useNotification } from "../@redux/hooks/site";
import store from "../@redux/store";
import { LoadingIndicator, ModalProvider } from "../components";
import Router from "../Router";
import Sidebar from "../Sidebar";
import Auth from "../special-pages/AuthPage";
import ErrorBoundary from "../special-pages/ErrorBoundary";
import LaunchError from "../special-pages/LaunchError";
import { Environment } from "../utilities";
import Header from "./Header";

// Sidebar Toggle

interface Props {}

const App: FunctionComponent<Props> = () => {
  const { initialized, auth } = useReduxStore((s) => s.site);

  const notify = useNotification("has-update", 10 * 1000);

  // Has any update?
  useEffectOnceWhen(() => {
    if (Environment.hasUpdate) {
      notify({
        type: "info",
        message: "A new version of Bazarr is ready, restart is required",
        // TODO: Restart action
      });
    }
  }, initialized === true);

  if (!auth) {
    return <Redirect to="/login"></Redirect>;
  }

  if (typeof initialized === "boolean" && initialized === false) {
    return (
      <LoadingIndicator>
        <span>Please wait</span>
      </LoadingIndicator>
    );
  } else if (typeof initialized === "string") {
    return <LaunchError>{initialized}</LaunchError>;
  }
  return (
    <ErrorBoundary>
      <Row noGutters className="header-container">
        <Header></Header>
      </Row>
      <Row noGutters className="flex-nowrap">
        <Sidebar></Sidebar>
        <ModalProvider>
          <Router></Router>
        </ModalProvider>
      </Row>
    </ErrorBoundary>
  );
};

const MainRouter: FunctionComponent = () => {
  useEffect(() => {
    Socketio.initialize();
  }, []);

  return (
    <BrowserRouter basename={Environment.baseUrl}>
      <Switch>
        <Route exact path="/login">
          <Auth></Auth>
        </Route>
        <Route path="/">
          <App></App>
        </Route>
      </Switch>
    </BrowserRouter>
  );
};

const Main: FunctionComponent = () => {
  return (
    <Provider store={store}>
      {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
      {/* <React.StrictMode> */}
      <MainRouter></MainRouter>
      {/* </React.StrictMode> */}
    </Provider>
  );
};

export default Main;
