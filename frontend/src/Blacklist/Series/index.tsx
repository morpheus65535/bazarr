import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { updateSeriesBlacklist } from "../../@redux/actions";
import { ContentHeader } from "../../components";
import Table from "./table";
import { SeriesApi } from "../../apis";

interface Props {
  update: () => void;
}

const BlacklistSeriesView: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);
  return (
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
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(undefined, { update: updateSeriesBlacklist })(
  BlacklistSeriesView
);
