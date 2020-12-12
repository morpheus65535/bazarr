import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";

import { connect } from "react-redux";
import { updateWantedMovieList } from "../../@redux/actions";

import { faSearch } from "@fortawesome/free-solid-svg-icons";

import Table from "./table";

import { ContentHeader, ContentHeaderButton } from "../../components";

interface Props {
  update: () => void;
}

class WantedMoviesView extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render() {
    return (
      <Container fluid>
        <Helmet>
          <title>Wanted Movies - Bazarr</title>
        </Helmet>
        <Row>
          <ContentHeader>
            <ContentHeaderButton iconProps={{ icon: faSearch }}>
              Search All
            </ContentHeaderButton>
          </ContentHeader>
        </Row>
        <Row>
          <Table></Table>
        </Row>
      </Container>
    );
  }
}

export default connect(null, { update: updateWantedMovieList })(
  WantedMoviesView
);
