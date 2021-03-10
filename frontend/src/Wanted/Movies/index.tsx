import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useWantedMovies } from "../../@redux/hooks";
import { MoviesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import { useAutoUpdate } from "../../utilites/hooks";
import Table from "./table";

interface Props {}

const WantedMoviesView: FunctionComponent<Props> = () => {
  const [wanted, update] = useWantedMovies();
  useAutoUpdate(update);

  return (
    <AsyncStateOverlay state={wanted}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Wanted Movies - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              disabled={data.length === 0}
              promise={() => MoviesApi.action({ action: "search-wanted" })}
              onSuccess={update as () => void}
              icon={faSearch}
            >
              Search All
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <Table wanted={data} update={update}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default WantedMoviesView;
