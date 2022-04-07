import AppNavbar from "@/App/Navbar";
import ErrorBoundary from "@/components/ErrorBoundary";
import { Layout } from "@/constants";
import ModalsProvider from "@/modules/modals/ModalsProvider";
import { useNotification } from "@/modules/redux/hooks";
import { useReduxStore } from "@/modules/redux/hooks/base";
import SocketIO from "@/modules/socketio";
import LaunchError from "@/pages/LaunchError";
import { Environment } from "@/utilities";
import { AppShell, LoadingOverlay } from "@mantine/core";
import { FunctionComponent, useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useEffectOnceWhen } from "rooks";
import AppHeader from "./Header";
import ThemeProvider from "./theme";

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
  } else if (status === "error") {
    return <LaunchError>Cannot Initialize Bazarr</LaunchError>;
  }

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ModalsProvider>
          <LoadingOverlay visible={status === "uninitialized"}></LoadingOverlay>
          <AppShell
            navbarOffsetBreakpoint={Layout.MOBILE_BREAKPOINT}
            header={<AppHeader></AppHeader>}
            navbar={<AppNavbar></AppNavbar>}
            padding={0}
            fixed
          >
            <Outlet></Outlet>
          </AppShell>
        </ModalsProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
