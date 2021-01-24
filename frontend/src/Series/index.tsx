import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { faList } from "@fortawesome/free-solid-svg-icons";
import { Helmet } from "react-helmet";

import { ContentHeader, ContentHeaderButton } from "../components";
import Table from "./table";

interface Props {}

const SeriesView: FunctionComponent<Props> = () => {
  return (
    <Container fluid>
      <Helmet>
        <title>Series - Bazarr</title>
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

export default SeriesView;
