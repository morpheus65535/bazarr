import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";

import { connect } from "react-redux";
import { updateWantedSeriesList } from "../../@redux/actions";

import { faSearch } from "@fortawesome/free-solid-svg-icons";

import { ContentHeader, ContentHeaderButton } from "../../components";

import Table from "./table";

interface Props {
  update: () => void;
}

const WantedSeriesView: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);
  return (
    <Container fluid>
      <Helmet>
        <title>Wanted Series - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeaderButton icon={faSearch}>Search All</ContentHeaderButton>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(null, {
  update: updateWantedSeriesList,
})(WantedSeriesView);
