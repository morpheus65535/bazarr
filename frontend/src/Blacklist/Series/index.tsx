import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { seriesUpdateBlacklist } from "../../@redux/actions";
import { SeriesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  blacklist: AsyncState<SeriesBlacklist[]>;
  update: () => void;
}

function mapStateToProps({ series }: StoreState) {
  return {
    blacklist: series.blacklist,
  };
}

const BlacklistSeriesView: FunctionComponent<Props> = ({
  update,
  blacklist,
}) => {
  useEffect(() => update(), [update]);
  return (
    <AsyncStateOverlay state={blacklist}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Series Blacklist - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              icon={faTrash}
              promise={() => SeriesApi.deleteBlacklist(true)}
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

export default connect(mapStateToProps, { update: seriesUpdateBlacklist })(
  BlacklistSeriesView
);
