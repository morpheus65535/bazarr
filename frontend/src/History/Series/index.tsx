import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSeriesHistory } from "../../@redux/hooks";
import { useAutoUpdate } from "../../utilites/hooks";
import Table from "./table";

interface Props {}

const SeriesHistoryView: FunctionComponent<Props> = () => {
  const [, update] = useSeriesHistory();
  useAutoUpdate(update);

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
