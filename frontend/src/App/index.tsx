import React from "react";
import { Container, Row } from "react-bootstrap";
import { BrowserRouter } from "react-router-dom";
import Router from "./Router";
import Sidebar from "../Sidebar";
import Header from "./Header";

import "../@scss/index.scss";

import { updateBadges, updateLanguagesList } from "../@redux/actions";
import { connect } from "react-redux";

interface Props {
  updateBadges: () => void;
  updateLanguagesList: (enabled: boolean) => void;
}

interface State {
  sidebarOpen: boolean;
}

// function mapStateToProps({ series, movie, system }: StoreState) {
//   return {
//     init: series.seriesList.
//   };
// }

class App extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      sidebarOpen: false,
    };
  }
  componentDidMount() {
    // Initialize Here
    this.props.updateBadges();
    this.props.updateLanguagesList(false);
  }

  toggleSidebar() {
    this.setState((s) => ({
      ...s,
      sidebarOpen: !s.sidebarOpen,
    }));
  }

  render() {
    const { sidebarOpen } = this.state;

    let baseUrl =
      process.env.NODE_ENV === "production" ? window.Bazarr.baseUrl : "/";
    return (
      <div id="app">
        <BrowserRouter basename={baseUrl}>
          <Container fluid className="p-0">
            <Row noGutters className="header-container">
              <Header onToggle={this.toggleSidebar.bind(this)}></Header>
            </Row>
            <Row noGutters className="flex-nowrap">
              <Sidebar
                open={sidebarOpen}
                onToggle={this.toggleSidebar.bind(this)}
              ></Sidebar>
              <Router className="d-flex flex-row flex-grow-1 main-router"></Router>
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
