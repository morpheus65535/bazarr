import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { movieUpdateBlacklist } from "../../@redux/actions";
import { MoviesApi } from "../../apis";
import { ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  update: () => void;
}

const BlacklistMoviesView: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);
  return (
    <Container fluid>
      <Helmet>
        <title>Movies Blacklist - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.AsyncButton
          icon={faTrash}
          promise={() => MoviesApi.deleteBlacklist(true)}
          onSuccess={update}
        >
          Remove All
        </ContentHeader.AsyncButton>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(undefined, { update: movieUpdateBlacklist })(
  BlacklistMoviesView
);
