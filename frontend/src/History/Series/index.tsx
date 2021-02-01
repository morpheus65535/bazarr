import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { seriesUpdateHistoryList } from "../../@redux/actions";
import Table from "./table";

interface Props {
  update: () => void;
}

const SeriesHistoryView: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);

  return (
    <Container fluid>
      <Helmet>
        <title>Series History - Bazarr</title>
      </Helmet>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(null, { update: seriesUpdateHistoryList })(
  SeriesHistoryView
);
