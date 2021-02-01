import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { movieUpdateHistoryList } from "../../@redux/actions";
import Table from "./table";

interface Props {
  update: () => void;
}

const MoviesHistoryView: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);

  return (
    <Container fluid>
      <Helmet>
        <title>Movies History - Bazarr</title>
      </Helmet>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(null, { update: movieUpdateHistoryList })(
  MoviesHistoryView
);
