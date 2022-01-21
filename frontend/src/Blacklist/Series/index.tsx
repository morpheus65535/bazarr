import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import api from "src/apis/raw";
import { useEpisodeBlacklist } from "../../apis/hooks/series";
import { ContentHeader, QueryOverlay } from "../../components";
import Table from "./table";

interface Props {}

const BlacklistSeriesView: FunctionComponent<Props> = () => {
  const blacklist = useEpisodeBlacklist();
  const { data } = blacklist;
  return (
    <QueryOverlay result={blacklist}>
      <Container fluid>
        <Helmet>
          <title>Series Blacklist - Bazarr</title>
        </Helmet>
        <ContentHeader>
          <ContentHeader.AsyncButton
            icon={faTrash}
            disabled={data?.length === 0}
            promise={() => api.episodes.deleteBlacklist(true)}
          >
            Remove All
          </ContentHeader.AsyncButton>
        </ContentHeader>
        <Row>
          <Table blacklist={data ?? []}></Table>
        </Row>
      </Container>
    </QueryOverlay>
  );
};

export default BlacklistSeriesView;
