import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { seriesUpdateWantedAll } from "../../@redux/actions";
import { EpisodesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  wanted: AsyncState<WantedEpisode[]>;
  update: () => void;
}

function mapStateToProps({ series }: StoreState) {
  const { wantedSeriesList } = series;
  return {
    wanted: wantedSeriesList,
  };
}

const WantedSeriesView: FunctionComponent<Props> = ({ update, wanted }) => {
  useEffect(() => update(), [update]);
  return (
    <AsyncStateOverlay state={wanted}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Wanted Series - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              promise={() => EpisodesApi.searchAllWanted()}
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

export default connect(mapStateToProps, {
  update: seriesUpdateWantedAll,
})(WantedSeriesView);
