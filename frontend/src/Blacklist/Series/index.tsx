import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { EpisodesApi } from "../../apis";
import { useEpisodeBlacklist } from "../../apis/hooks/series";
import { ContentHeader, QueryOverlay } from "../../components";
import Table from "./table";

interface Props {}

const BlacklistSeriesView: FunctionComponent<Props> = () => {
  const blacklist = useEpisodeBlacklist();
  return (
    <QueryOverlay {...blacklist}>
      {({ data }) => (
        <Container fluid>
          <Helmet>
            <title>Series Blacklist - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              icon={faTrash}
              disabled={data?.length === 0}
              promise={() => EpisodesApi.deleteBlacklist(true)}
            >
              Remove All
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <Table blacklist={data ?? []}></Table>
          </Row>
        </Container>
      )}
    </QueryOverlay>
  );
};

export default BlacklistSeriesView;
