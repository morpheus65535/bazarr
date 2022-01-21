import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import api from "src/apis/raw";
import { useMovieBlacklist } from "../../apis/hooks/movies";
import { ContentHeader, QueryOverlay } from "../../components";
import Table from "./table";

interface Props {}

const BlacklistMoviesView: FunctionComponent<Props> = () => {
  const blacklist = useMovieBlacklist();
  return (
    <QueryOverlay {...blacklist}>
      {({ data }) => (
        <Container fluid>
          <Helmet>
            <title>Movies Blacklist - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              icon={faTrash}
              disabled={data?.length === 0}
              promise={() => api.movies.deleteBlacklist(true)}
            >
              Remove All
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <Table blacklist={data ?? []}></Table>
          </Row>
        </Container>
      )}
    </QueryOverlay>
  );
};

export default BlacklistMoviesView;
