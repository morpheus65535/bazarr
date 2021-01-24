import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";

import { faList } from "@fortawesome/free-solid-svg-icons";

import { ContentHeader, ContentHeaderButton } from "../components";

import Table from "./table";

interface Props {}
const MovieView: FunctionComponent<Props> = () => {
  return (
    <Container fluid>
      <Helmet>
        <title>Movies - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeaderButton icon={faList}>Mass Edit</ContentHeaderButton>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default MovieView;
