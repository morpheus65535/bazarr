import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { BrowserRouter } from "react-router-dom";
import Router from "./Router";
import Sidebar from "../Sidebar";
import Header from "./Header";

import "./App.css";

import { updateBadges, updateLanguagesList } from "../@redux/actions";
import { connect } from "react-redux";

interface Props {
  updateBadges: () => void;
  updateLanguagesList: (enabled: boolean) => void;
}

// function mapStateToProps({ series, movie, system }: StoreState) {
//   return {
//     init: series.seriesList.
//   };
// }

class App extends React.Component<Props> {
  componentDidMount() {
    // Initialize Here
    this.props.updateBadges();
    this.props.updateLanguagesList(false);
  }

  render() {
    let baseUrl =
      process.env.NODE_ENV === "production" ? window.Bazarr.baseUrl : "/";
    return (
      <div id="app">
        <BrowserRouter basename={baseUrl}>
          <Container fluid className="p-0">
            <Row>
              <Header></Header>
            </Row>
            <Row noGutters>
              <Col sm={12} md={3} lg={2}>
                <Sidebar></Sidebar>
              </Col>
              <Col>
                <Router></Router>
              </Col>
            </Row>
          </Container>
        </BrowserRouter>
      </div>
    );
  }
}

export default connect(null, {
  updateBadges,
  updateLanguagesList,
})(App);
