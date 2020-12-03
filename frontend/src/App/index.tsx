import React from "react";
import { Container } from "react-bootstrap";
import { BrowserRouter } from "react-router-dom";
import Router from "./Router";
import Sidebar from "./Sidebar";
import Header from "./Header";

import "./App.css";

import {
  updateEpisodes,
  updateMovies,
  updateProviders,
} from "../@redux/actions/badges";
import { updateLanguagesList } from "../@redux/actions/system";
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
    return (
      <div id="app">
        <BrowserRouter>
          <Container fluid className="p-0 d-flex">
            <Sidebar></Sidebar>
            <div id="content-wrapper">
              <Header></Header>
              <Router></Router>
            </div>
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
