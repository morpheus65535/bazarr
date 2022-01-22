import { LoadingIndicator, ModalProvider } from "@/components";
import { useNotification } from "@/modules/redux/hooks";
import { useReduxStore } from "@/modules/redux/hooks/base";
import SocketIO from "@/modules/socketio";
import LaunchError from "@/pages/LaunchError";
import { Environment } from "@/utilities";
import React, { FunctionComponent, useEffect } from "react";
import { Row } from "react-bootstrap";
import { BrowserRouter as Router, useRoutes } from "react-router-dom";
import { useEffectOnceWhen } from "rooks";
import ErrorBoundary from "../components/ErrorBoundary";
import { routes } from "../Router";
import Sidebar from "../Sidebar";
import Header from "./Header";

const RouteApp: FunctionComponent = () => useRoutes(routes);

const App: FunctionComponent = () => {
  const { status } = useReduxStore((s) => s);

  useEffect(() => {
    SocketIO.initialize();
  }, []);

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
    return <div>TODO: Login Windows</div>;
    // return <Navigate to="/login"></Navigate>;
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
      <Router>
        <Row noGutters className="header-container">
          <Header></Header>
        </Row>
        <Row noGutters className="flex-nowrap">
          <Sidebar></Sidebar>
          <ModalProvider>
            <RouteApp></RouteApp>
          </ModalProvider>
        </Row>
      </Router>
    </ErrorBoundary>
  );
};

export default App;
