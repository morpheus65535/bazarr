import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Row } from "react-bootstrap";
import { Redirect } from "react-router-dom";
import { useReduxStore } from "../@redux/hooks/base";
import { useNotification } from "../@redux/hooks/site";
import { LoadingIndicator, ModalProvider } from "../components";
import Sidebar from "../Sidebar";
import LaunchError from "../special-pages/LaunchError";
import UIError from "../special-pages/UIError";
import { useHasUpdateInject } from "../utilites";
import Header from "./Header";
import NotificationContainer from "./notifications";
import Router from "./Router";

// Sidebar Toggle
export const SidebarToggleContext = React.createContext<() => void>(() => {});

interface Props {}

const App: FunctionComponent<Props> = () => {
  const { initialized, auth } = useReduxStore((s) => s.site);

  const notify = useNotification("has-update", 10);

  // Has any update?
  const hasUpdate = useHasUpdateInject();
  useEffect(() => {
    if (initialized) {
      if (hasUpdate) {
        notify({
          type: "info",
          message: "A new version of Bazarr is ready, restart is required",
          // TODO: Restart action
        });
      }
    }
  }, [initialized, hasUpdate, notify]);

  const [sidebar, setSidebar] = useState(false);
  const toggleSidebar = useCallback(() => setSidebar((s) => !s), []);

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
  try {
    return (
      <SidebarToggleContext.Provider value={toggleSidebar}>
        <Row noGutters className="header-container">
          <Header></Header>
        </Row>
        <Row noGutters className="flex-nowrap">
          <Sidebar open={sidebar}></Sidebar>
          <ModalProvider>
            <Router className="d-flex flex-row flex-grow-1 main-router"></Router>
          </ModalProvider>
        </Row>
        <NotificationContainer></NotificationContainer>
      </SidebarToggleContext.Provider>
    );
  } catch (e) {
    return <UIError error={e}></UIError>;
  }
};

export default App;
