import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { movieUpdateInfoAll } from "../../@redux/actions";
import { MoviesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import { useWantedMovies } from "../../utilites/items";
import Table from "./table";

interface Props {
  update: () => void;
}

const WantedMoviesView: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);

  const wanted = useWantedMovies();

  return (
    <AsyncStateOverlay state={wanted}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Wanted Movies - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              promise={() => MoviesApi.action({ action: "search-wanted" })}
              onSuccess={update}
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

export default connect(undefined, { update: movieUpdateInfoAll })(
  WantedMoviesView
);
