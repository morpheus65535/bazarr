import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useItemUpdater, useSeriesHistory } from "../../@redux/hooks";
import Table from "./table";

interface Props {}

const SeriesHistoryView: FunctionComponent<Props> = () => {
  const [, update] = useSeriesHistory();
  useItemUpdater(update);

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

export default SeriesHistoryView;
