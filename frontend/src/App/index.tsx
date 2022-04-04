import Navbar from "@/App/Navbar";
import { LoadingIndicator } from "@/components";
import ErrorBoundary from "@/components/ErrorBoundary";
import { Layout } from "@/constants";
import { useNotification } from "@/modules/redux/hooks";
import { useReduxStore } from "@/modules/redux/hooks/base";
import SocketIO from "@/modules/socketio";
import LaunchError from "@/pages/LaunchError";
import { Environment } from "@/utilities";
import { AppShell } from "@mantine/core";
import { FunctionComponent, useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useEffectOnceWhen } from "rooks";
import Header from "./Header";

const App: FunctionComponent = () => {
  const { status } = useReduxStore((s) => s.site);

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
    return <Navigate to="/login"></Navigate>;
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
      <AppShell
        navbarOffsetBreakpoint={Layout.MOBILE_BREAKPOINT}
        header={<Header></Header>}
        navbar={<Navbar></Navbar>}
        padding={0}
      >
        <Outlet></Outlet>
      </AppShell>
    </ErrorBoundary>
  );
};

export default App;
