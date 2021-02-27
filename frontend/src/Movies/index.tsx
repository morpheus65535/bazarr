import { faList } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { AsyncStateOverlay, ContentHeader } from "../components";
import Table from "./table";

interface Props {
  movies: AsyncState<Movie[]>;
}

function mapStateToProps({ movie }: StoreState) {
  const { movieList } = movie;
  return {
    movies: movieList,
  };
}

const MovieView: FunctionComponent<Props> = ({ movies }) => {
  return (
    <AsyncStateOverlay state={movies}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Movies - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button icon={faList}>Mass Edit</ContentHeader.Button>
          </ContentHeader>
          <Row>
            <Table movies={data}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(MovieView);
