import AppNavbar from "@/App/Navbar";
import ErrorBoundary from "@/components/ErrorBoundary";
import { Layout } from "@/constants";
import { useNotification } from "@/modules/redux/hooks";
import { useReduxStore } from "@/modules/redux/hooks/base";
import SocketIO from "@/modules/socketio";
import LaunchError from "@/pages/LaunchError";
import { Environment } from "@/utilities";
import { AppShell, Header, LoadingOverlay, Navbar } from "@mantine/core";
import { FunctionComponent, useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useEffectOnceWhen } from "rooks";
import AppHeader from "./Header";

const App: FunctionComponent = () => {
  const { status, showSidebar } = useReduxStore((s) => s.site);

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
  } else if (status === "error") {
    return <LaunchError>Cannot Initialize Bazarr</LaunchError>;
  }

  return (
    <ErrorBoundary>
      <LoadingOverlay visible={status === "uninitialized"}></LoadingOverlay>
      <AppShell
        navbarOffsetBreakpoint={Layout.MOBILE_BREAKPOINT}
        header={
          <Header p="md" height={Layout.HEADER_HEIGHT}>
            <AppHeader></AppHeader>
          </Header>
        }
        navbar={
          <Navbar
            p="xs"
            hiddenBreakpoint={Layout.MOBILE_BREAKPOINT}
            hidden={!showSidebar}
            width={{ [Layout.MOBILE_BREAKPOINT]: Layout.NAVBAR_WIDTH }}
          >
            <AppNavbar></AppNavbar>
          </Navbar>
        }
        padding={0}
        fixed
      >
        <Outlet></Outlet>
      </AppShell>
    </ErrorBoundary>
  );
};

export default App;
