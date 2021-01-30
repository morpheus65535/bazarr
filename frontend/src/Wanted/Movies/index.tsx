import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";

import { connect } from "react-redux";
import { movieUpdateWantedAll } from "../../@redux/actions";

import { faSearch } from "@fortawesome/free-solid-svg-icons";

import Table from "./table";

import { ContentHeader } from "../../components";

import { MoviesApi } from "../../apis";

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
        <ContentHeader.AsyncButton
          promise={() => MoviesApi.searchAllWanted()}
          onSuccess={update}
          icon={faSearch}
        >
          Search All
        </ContentHeader.AsyncButton>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(null, { update: movieUpdateWantedAll })(
  WantedMoviesView
);
