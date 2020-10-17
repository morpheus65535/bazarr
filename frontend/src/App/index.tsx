import React from "react";
import { Container } from "react-bootstrap";
import { BrowserRouter } from "react-router-dom";
import Router from "./Router";
import Sidebar from "./Sidebar";
import Header from "./Header";

import "./App.css";

import apis from "../apis";

import {
  updateEpisodes,
  updateMovies,
  updateProviders,
} from "../redux/actions/badges";
import { connect } from "react-redux";

interface Props {
  updateEpisodes: (val: number) => void;
  updateMovies: (val: number) => void;
  updateProviders: (val: number) => void;
}

class App extends React.Component<Props, {}> {
  componentDidMount() {
    apis.badges.movies().then((val) => {
      this.props.updateMovies(val);
    });

    apis.badges.series().then((val) => {
      this.props.updateEpisodes(val);
    });

    apis.badges.providers().then((val) => {
      this.props.updateProviders(val);
    });
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

export default connect(null, { updateEpisodes, updateMovies, updateProviders })(
  App
);
