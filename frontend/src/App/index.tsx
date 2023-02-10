import AppNavbar from "@/App/Navbar";
import ErrorBoundary from "@/components/ErrorBoundary";
import { Layout } from "@/constants";
import NavbarProvider from "@/contexts/Navbar";
import OnlineProvider from "@/contexts/Online";
import { notification } from "@/modules/task";
import CriticalError from "@/pages/errors/CriticalError";
import { RouterNames } from "@/Router/RouterNames";
import { Environment } from "@/utilities";
import { AppShell } from "@mantine/core";
import { useWindowEvent } from "@mantine/hooks";
import { showNotification } from "@mantine/notifications";
import { FunctionComponent, useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import AppHeader from "./Header";

const App: FunctionComponent = () => {
  const navigate = useNavigate();

  const [criticalError, setCriticalError] = useState<string | null>(null);
  const [navbar, setNavbar] = useState(false);
  const [online, setOnline] = useState(true);

  useWindowEvent("app-critical-error", ({ detail }) => {
    setCriticalError(detail.message);
  });

  useWindowEvent("app-auth-changed", (ev) => {
    if (!ev.detail.authenticated) {
      navigate(RouterNames.Auth);
    }
  });

  useWindowEvent("app-online-status", ({ detail }) => {
    setOnline(detail.online);
  });

  useEffect(() => {
    if (Environment.hasUpdate) {
      showNotification(
        notification.info(
          "Update available",
          "A new version of Bazarr is ready, restart is required"
        )
      );
    }
  }, []);

  if (criticalError !== null) {
    return <CriticalError message={criticalError}></CriticalError>;
  }

  return (
    <ErrorBoundary>
      <NavbarProvider value={{ showed: navbar, show: setNavbar }}>
        <OnlineProvider value={{ online, setOnline }}>
          <AppShell
            navbarOffsetBreakpoint={Layout.MOBILE_BREAKPOINT}
            header={<AppHeader></AppHeader>}
            navbar={<AppNavbar></AppNavbar>}
            padding={0}
            fixed
          >
            <Outlet></Outlet>
          </AppShell>
        </OnlineProvider>
      </NavbarProvider>
    </ErrorBoundary>
  );
};

export default App;
