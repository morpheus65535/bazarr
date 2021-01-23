import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Container, Row } from "react-bootstrap";
import { BrowserRouter } from "react-router-dom";
import Router from "./Router";
import Sidebar from "../Sidebar";
import Header from "./Header";

import { bootstrap } from "../@redux/actions";
import { connect } from "react-redux";

import { LoadingIndicator } from "../Components";

interface Props {
  bootstrap: () => void;
  initialized: boolean;
}

function mapStateToProps({ system }: StoreState) {
  return {
    initialized: system.initialized,
  };
}

const App: FunctionComponent<Props> = ({ bootstrap, initialized }) => {
  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const [sidebar, setSidebar] = useState(false);

  const toggleSidebar = useCallback(() => setSidebar(!sidebar), [sidebar]);

  const baseUrl =
    process.env.NODE_ENV === "production" ? window.Bazarr.baseUrl : "/";

  if (!initialized) {
    return (
      <LoadingIndicator>
        <span>Please wait</span>
      </LoadingIndicator>
    );
  }

  return (
    <React.Fragment>
      <BrowserRouter basename={baseUrl}>
        <Container fluid className="p-0">
          <Row noGutters className="header-container">
            <Header onToggle={toggleSidebar}></Header>
          </Row>
          <Row noGutters className="flex-nowrap">
            <Sidebar open={sidebar} onToggle={toggleSidebar}></Sidebar>
            <Router className="d-flex flex-row flex-grow-1 main-router"></Router>
          </Row>
        </Container>
      </BrowserRouter>
    </React.Fragment>
  );
};

export default connect(mapStateToProps, {
  bootstrap,
})(App);
