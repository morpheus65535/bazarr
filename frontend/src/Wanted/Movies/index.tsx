import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { movieUpdateWantedAll } from "../../@redux/actions";
import { MoviesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  wanted: AsyncState<Wanted.Movie[]>;
  update: () => void;
}

function mapStateToProps({ movie }: ReduxStore) {
  const { wantedMovieList } = movie;
  return {
    wanted: wantedMovieList,
  };
}

const WantedMoviesView: FunctionComponent<Props> = ({ update, wanted }) => {
  useEffect(() => update(), [update]);

  return (
    <AsyncStateOverlay state={wanted}>
      {(data) => (
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
            <Table wanted={data}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: movieUpdateWantedAll })(
  WantedMoviesView
);
