import React from "react";
import { Container } from "react-bootstrap";
import { connect } from "react-redux";

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
      <Container fluid className="m-1">
        <Table></Table>
      </Container>
    );
  }
}

export default connect(null, { update: updateHistoryMovieList })(
  MoviesHistoryView
);
