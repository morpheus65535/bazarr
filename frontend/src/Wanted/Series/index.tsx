import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { seriesUpdateWantedAll } from "../../@redux/actions";
import { SeriesApi } from "../../apis";
import { ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  update: () => void;
}

const WantedSeriesView: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);
  return (
    <Container fluid>
      <Helmet>
        <title>Wanted Series - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.AsyncButton
          promise={() => SeriesApi.searchAllWanted()}
          onSuccess={update}
          icon={faSearch}
        >
          Search All
        </ContentHeader.AsyncButton>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(null, {
  update: seriesUpdateWantedAll,
})(WantedSeriesView);
