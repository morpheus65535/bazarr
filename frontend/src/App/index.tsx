import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Row } from "react-bootstrap";
import { Redirect } from "react-router-dom";
import { bootstrap as ReduxBootstrap } from "../@redux/actions";
import { useReduxAction, useReduxStore } from "../@redux/hooks/base";
import { LoadingIndicator, ModalProvider } from "../components";
import Sidebar from "../Sidebar";
import Header from "./Header";
import Router from "./Router";

// Sidebar Toggle
export const SidebarToggleContext = React.createContext<() => void>(() => {});

interface Props {}

const App: FunctionComponent<Props> = () => {
  const bootstrap = useReduxAction(ReduxBootstrap);

  const { initialized, authState } = useReduxStore((s) => ({
    initialized: s.site.initialized,
    authState: s.site.auth,
  }));

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const [sidebar, setSidebar] = useState(false);
  const toggleSidebar = useCallback(() => setSidebar(!sidebar), [sidebar]);

  if (!authState) {
    return <Redirect to="/login"></Redirect>;
  }

  // TODO: Error handling on initializing process
  if (!initialized) {
    return (
      <LoadingIndicator>
        <span>Please wait</span>
      </LoadingIndicator>
    );
  }

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
    </SidebarToggleContext.Provider>
  );
};

export default App;
