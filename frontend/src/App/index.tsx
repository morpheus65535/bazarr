import { LoadingIndicator, ModalProvider } from "@/components";
import { useNotification } from "@/modules/redux/hooks";
import { useReduxStore } from "@/modules/redux/hooks/base";
import Socketio from "@/modules/socketio";
import Authentication from "@/pages/Authentication";
import LaunchError from "@/pages/LaunchError";
import { Environment } from "@/utilities";
import React, { FunctionComponent, useEffect } from "react";
import { Row } from "react-bootstrap";
import { Route, Switch } from "react-router";
import { BrowserRouter, Redirect } from "react-router-dom";
import { useEffectOnceWhen } from "rooks";
import ErrorBoundary from "../components/ErrorBoundary";
import Router from "../Router";
import Sidebar from "../Sidebar";
import Header from "./Header";

// Sidebar Toggle

interface Props {}

const App: FunctionComponent<Props> = () => {
  const { status } = useReduxStore((s) => s);

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
  }, status === "initialized");

  if (status === "unauthenticated") {
    return <Redirect to="/login"></Redirect>;
  } else if (status === "uninitialized") {
    return (
      <LoadingIndicator>
        <span>Please wait</span>
      </LoadingIndicator>
    );
  } else if (status === "error") {
    return <LaunchError>Cannot Initialize Bazarr</LaunchError>;
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
