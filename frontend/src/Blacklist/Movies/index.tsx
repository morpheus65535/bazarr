import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { movieUpdateBlacklist } from "../../@redux/actions";
import { MoviesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  blacklist: AsyncState<Blacklist.Movie[]>;
  update: () => void;
}

function mapStateToProps({ movie }: ReduxStore) {
  return {
    blacklist: movie.blacklist,
  };
}

const BlacklistMoviesView: FunctionComponent<Props> = ({
  update,
  blacklist,
}) => {
  useEffect(() => update(), [update]);
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
            <Table blacklist={data}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: movieUpdateBlacklist })(
  BlacklistMoviesView
);
