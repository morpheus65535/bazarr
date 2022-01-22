import Socketio from "@modules/socketio";
import { useNotification } from "@redux/hooks";
import { useReduxStore } from "@redux/hooks/base";
import { LoadingIndicator, ModalProvider } from "components";
import Authentication from "pages/Authentication";
import LaunchError from "pages/LaunchError";
import React, { FunctionComponent, useEffect } from "react";
import { Row } from "react-bootstrap";
import { Route, Switch } from "react-router";
import { BrowserRouter, Redirect } from "react-router-dom";
import { useEffectOnceWhen } from "rooks";
import { Environment } from "utilities";
import ErrorBoundary from "../components/ErrorBoundary";
import Router from "../Router";
import Sidebar from "../Sidebar";
import Header from "./Header";

// Sidebar Toggle

interface Props {}

const App: FunctionComponent<Props> = () => {
  const { initialized, auth } = useReduxStore((s) => s);

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
          <Authentication></Authentication>
        </Route>
        <Route path="/">
          <App></App>
        </Route>
      </Switch>
    </BrowserRouter>
  );
};

export default MainRouter;
