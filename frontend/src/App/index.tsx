import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { BrowserRouter } from "react-router-dom";
import Router from "./Router";
import Sidebar from "./Sidebar";
import Header from "./Header";

import "./App.css";

import {
  updateEpisodes,
  updateMovies,
  updateProviders,
  updateLanguagesList,
} from "../@redux/actions";
import { connect } from "react-redux";

interface Props {
  updateEpisodes: () => void;
  updateMovies: () => void;
  updateProviders: () => void;
  updateLanguagesList: (enabled: boolean) => void;
}

class App extends React.Component<Props> {
  componentDidMount() {
    this.props.updateEpisodes();
    this.props.updateMovies();
    this.props.updateProviders();
    this.props.updateLanguagesList(false);
  }

  render() {
    const baseUrl = window.Bazarr.baseUrl
    return (
      <div id="app">
        <BrowserRouter basename={baseUrl}>
          <Container fluid className="p-0">
            <Row noGutters>
              <Col sm={12} md={3} lg={2}>
                <Sidebar></Sidebar>
              </Col>
              <Col>
                <Header></Header>
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
  updateEpisodes,
  updateMovies,
  updateProviders,
  updateLanguagesList,
})(App);
