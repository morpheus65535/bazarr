import AppNavbar from "@/App/Navbar";
import ErrorBoundary from "@/components/ErrorBoundary";
import { Layout } from "@/constants";
import ModalsProvider from "@/modules/modals/ModalsProvider";
import { useReduxStore } from "@/modules/redux/hooks/base";
import SocketIO from "@/modules/socketio";
import LaunchError from "@/pages/LaunchError";
import { Environment } from "@/utilities";
import { AppShell, LoadingOverlay } from "@mantine/core";
import {
  NotificationsProvider,
  showNotification,
} from "@mantine/notifications";
import { FunctionComponent, useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import AppHeader from "./Header";
import ThemeProvider from "./theme";

const App: FunctionComponent = () => {
  const { status } = useReduxStore((s) => s.site);

  useEffect(() => {
    SocketIO.initialize();
  }, []);

  useEffect(() => {
    if (Environment.hasUpdate && status === "initialized") {
      showNotification({
        title: "Update Available",
        message: "A new version of Bazarr is ready, restart is required",
      });
    }
  }, [status]);

  if (status === "unauthenticated") {
    return <Navigate to="/login"></Navigate>;
  } else if (status === "error") {
    return <LaunchError>Cannot Initialize Bazarr</LaunchError>;
  }

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ModalsProvider>
          <NotificationsProvider limit={5}>
            <LoadingOverlay
              visible={status === "uninitialized"}
            ></LoadingOverlay>
            <AppShell
              navbarOffsetBreakpoint={Layout.MOBILE_BREAKPOINT}
              header={<AppHeader></AppHeader>}
              navbar={<AppNavbar></AppNavbar>}
              padding={0}
              fixed
            >
              <Outlet></Outlet>
            </AppShell>
          </NotificationsProvider>
        </ModalsProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
