import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Alert, Button, Container, Row } from "react-bootstrap";
import { Redirect } from "react-router-dom";
import { bootstrap as ReduxBootstrap } from "../@redux/actions";
import { useReduxAction, useReduxStore } from "../@redux/hooks/base";
import { LoadingIndicator, ModalProvider } from "../components";
import Sidebar from "../Sidebar";
import { Reload } from "../utilites";
import Header from "./Header";
import NotificationContainer from "./notifications";
import Router from "./Router";

// Sidebar Toggle
export const SidebarToggleContext = React.createContext<() => void>(() => {});

interface Props {}

const App: FunctionComponent<Props> = () => {
  const bootstrap = useReduxAction(ReduxBootstrap);

  const { initialized, auth } = useReduxStore((s) => s.site);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const [sidebar, setSidebar] = useState(false);
  const toggleSidebar = useCallback(() => setSidebar(!sidebar), [sidebar]);

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
    return <InitializationErrorView>{initialized}</InitializationErrorView>;
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
      <NotificationContainer></NotificationContainer>
    </SidebarToggleContext.Provider>
  );
};

const InitializationErrorView: FunctionComponent<{
  children: string;
}> = ({ children }) => {
  return (
    <Container className="my-3">
      <Alert
        className="d-flex flex-nowrap justify-content-between align-items-center"
        variant="danger"
      >
        <div>
          <FontAwesomeIcon
            className="mr-2"
            icon={faExclamationTriangle}
          ></FontAwesomeIcon>
          <span>{children}</span>
        </div>
        <Button variant="outline-danger" onClick={Reload}>
          Reload
        </Button>
      </Alert>
    </Container>
  );
};

export default App;
