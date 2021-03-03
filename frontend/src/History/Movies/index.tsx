import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useItemUpdater, useMoviesHistory } from "../../@redux/hooks";
import Table from "./table";

interface Props {}

const MoviesHistoryView: FunctionComponent<Props> = () => {
  const [, update] = useMoviesHistory();
  useItemUpdater(update);

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

export default MoviesHistoryView;
