import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useBlacklistSeries } from "../../@redux/hooks";
import { EpisodesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {}

const BlacklistSeriesView: FunctionComponent<Props> = () => {
  const [blacklist] = useBlacklistSeries();
  return (
    <AsyncStateOverlay state={blacklist}>
      {({ data }) => (
        <Container fluid>
          <Helmet>
            <title>Series Blacklist - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              icon={faTrash}
              disabled={data.length === 0}
              promise={() => EpisodesApi.deleteBlacklist(true)}
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

export default BlacklistSeriesView;
