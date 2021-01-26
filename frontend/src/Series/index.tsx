import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { faList } from "@fortawesome/free-solid-svg-icons";
import { Helmet } from "react-helmet";

import { ContentHeader } from "../components";
import Table from "./table";

interface Props {}

const SeriesView: FunctionComponent<Props> = () => {
  return (
    <Container fluid>
      <Helmet>
        <title>Series - Bazarr</title>
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

export default SeriesView;
