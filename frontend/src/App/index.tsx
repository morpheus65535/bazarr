import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Container, Row } from "react-bootstrap";
import Router from "./Router";
import Sidebar from "../Sidebar";
import Header from "./Header";
import { bootstrap } from "../@redux/actions";
import { connect } from "react-redux";
import { LoadingIndicator, ModalProvider } from "../components";

// Sidebar Toggle
export const SidebarToggleContext = React.createContext<() => void>(() => {});

interface Props {
  bootstrap: () => void;
  initialized: boolean;
}

function mapStateToProps({ site }: StoreState) {
  return {
    initialized: site.initialized,
  };
}

const App: FunctionComponent<Props> = ({ bootstrap, initialized }) => {
  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const [sidebar, setSidebar] = useState(false);
  const toggleSidebar = useCallback(() => setSidebar(!sidebar), [sidebar]);

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
