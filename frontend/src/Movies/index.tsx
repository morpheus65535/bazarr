import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";

import { faList } from "@fortawesome/free-solid-svg-icons";

import { ContentHeader } from "../components";

import Table from "./table";

interface Props {}
const MovieView: FunctionComponent<Props> = () => {
  return (
    <Container fluid>
      <Helmet>
        <title>Movies - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Button icon={faList}>Mass Edit</ContentHeader.Button>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default MovieView;
