import React from "react";
import { Container } from "react-bootstrap";
import { BrowserRouter } from "react-router-dom";
import Router from "./Router";
import Sidebar from "./Sidebar";
import Header from "./Header";

import './App.css'

class App extends React.Component {
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

export default App;
