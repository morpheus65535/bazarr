import React, { FunctionComponent, useState } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { AsyncStateOverlay, ContentHeader } from "../components";
import EditModeHeader from "../components/EditModeHeader";
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
  const editMode = useState(false);

  return (
    <AsyncStateOverlay state={movies}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Movies - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <EditModeHeader editState={editMode}></EditModeHeader>
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
