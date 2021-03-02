import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Redirect } from "react-router-dom";
import { bootstrap } from "../@redux/actions";
import { LoadingIndicator, ModalProvider } from "../components";
import Sidebar from "../Sidebar";
import Header from "./Header";
import Router from "./Router";

// Sidebar Toggle
export const SidebarToggleContext = React.createContext<() => void>(() => {});

interface Props {
  bootstrap: () => void;
  initialized: boolean;
  authState: boolean;
}

function mapStateToProps({ site }: ReduxStore) {
  return {
    initialized: site.initialized,
    authState: site.auth,
  };
}

const App: FunctionComponent<Props> = ({
  bootstrap,
  initialized,
  authState,
}) => {
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
    <Container fluid className="p-0">
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
    </Container>
  );
};

export default connect(mapStateToProps, {
  bootstrap,
})(App);
