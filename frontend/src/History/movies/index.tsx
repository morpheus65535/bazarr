import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { updateHistoryMovieList } from "../../@redux/actions/movie";

import Table from "./table";

interface Props {
  update: () => void;
}

class MoviesHistoryView extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render() {
    return (
      <Container fluid>
        <Helmet>
          <title>Movies History - Bazarr</title>
        </Helmet>
        <Row className="flex-column">
          <Table></Table>
        </Row>
      </Container>
    );
  }
}

export default connect(null, { update: updateHistoryMovieList })(
  MoviesHistoryView
);
