import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useBlacklistMovies } from "../../@redux/hooks";
import { MoviesApi } from "../../apis";
import { AsyncOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {}

const BlacklistMoviesView: FunctionComponent<Props> = () => {
  const [blacklist] = useBlacklistMovies();
  return (
    <AsyncOverlay ctx={blacklist}>
      {({ content }) => (
        <Container fluid>
          <Helmet>
            <title>Movies Blacklist - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              icon={faTrash}
              disabled={content.length === 0}
              promise={() => MoviesApi.deleteBlacklist(true)}
            >
              Remove All
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <Table blacklist={content}></Table>
          </Row>
        </Container>
      )}
    </AsyncOverlay>
  );
};

export default BlacklistMoviesView;
