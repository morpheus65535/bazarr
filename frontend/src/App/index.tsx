import { FunctionComponent, useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router";
import { AppShell } from "@mantine/core";
import { useWindowEvent } from "@mantine/hooks";
import { showNotification } from "@mantine/notifications";
import AppNavbar from "@/App/Navbar";
import ErrorBoundary from "@/components/ErrorBoundary";
import NavbarProvider from "@/contexts/Navbar";
import OnlineProvider from "@/contexts/Online";
import { notification } from "@/modules/task";
import CriticalError from "@/pages/errors/CriticalError";
import { RouterNames } from "@/Router/RouterNames";
import { Environment } from "@/utilities";
import AppHeader from "./Header";
import styleVars from "@/assets/_variables.module.scss";

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
          "A new version of Bazarr is ready, restart is required",
        ),
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
            navbar={{
              width: styleVars.navBarWidth,
              breakpoint: "sm",
              collapsed: { mobile: !navbar },
            }}
            header={{ height: { base: styleVars.headerHeight } }}
            padding={0}
          >
            <AppHeader></AppHeader>
            <AppNavbar></AppNavbar>
            <AppShell.Main>
              <Outlet></Outlet>
            </AppShell.Main>
          </AppShell>
        </OnlineProvider>
      </NavbarProvider>
    </ErrorBoundary>
  );
};

export default App;
