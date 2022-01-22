import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useMovieBlacklist, useMovieDeleteBlacklist } from "apis/hooks/movies";
import { ContentHeader, QueryOverlay } from "components";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import Table from "./table";

interface Props {}

const BlacklistMoviesView: FunctionComponent<Props> = () => {
  const blacklist = useMovieBlacklist();
  const { data } = blacklist;

  const { mutateAsync } = useMovieDeleteBlacklist();

  return (
    <QueryOverlay result={blacklist}>
      <Container fluid>
        <Helmet>
          <title>Movies Blacklist - Bazarr</title>
        </Helmet>
        <ContentHeader>
          <ContentHeader.AsyncButton
            icon={faTrash}
            disabled={data?.length === 0}
            promise={() => mutateAsync({ all: true })}
          >
            Remove All
          </ContentHeader.AsyncButton>
        </ContentHeader>
        <Row>
          <Table blacklist={data ?? []}></Table>
        </Row>
      </Container>
    </QueryOverlay>
  );
};

export default BlacklistMoviesView;
