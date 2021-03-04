import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useBlacklistMovies } from "../../@redux/hooks";
import { MoviesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import { useAutoUpdate } from "../../utilites/hooks";
import Table from "./table";

interface Props {}

const BlacklistMoviesView: FunctionComponent<Props> = () => {
  const [blacklist, update] = useBlacklistMovies();
  useAutoUpdate(update);
  return (
    <AsyncStateOverlay state={blacklist}>
      {(data) => (
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
            <Table blacklist={data} update={update}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default BlacklistMoviesView;
