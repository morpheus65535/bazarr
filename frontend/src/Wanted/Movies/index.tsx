import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";

import { connect } from "react-redux";
import { updateWantedMovieList } from "../../@redux/actions";

import { faSearch } from "@fortawesome/free-solid-svg-icons";

import Table from "./table";

import { ContentHeader } from "../../components";

interface Props {
  update: () => void;
}

const WantedMoviesView: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);

  return (
    <Container fluid>
      <Helmet>
        <title>Wanted Movies - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Button icon={faSearch}>Search All</ContentHeader.Button>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(null, { update: updateWantedMovieList })(
  WantedMoviesView
);
