import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useBlacklistSeries } from "../../@redux/hooks";
import { EpisodesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {}

const BlacklistSeriesView: FunctionComponent<Props> = () => {
  const [blacklist, update] = useBlacklistSeries();
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
              promise={() => EpisodesApi.deleteBlacklist(true)}
              onSuccess={update}
            >
              Remove All
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <Table blacklist={data} update={update}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default BlacklistSeriesView;
