import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useEpisodeBlacklist, useEpisodeDeleteBlacklist } from "apis/hooks";
import { ContentHeader, QueryOverlay } from "components";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import Table from "./table";

interface Props {}

const BlacklistSeriesView: FunctionComponent<Props> = () => {
  const blacklist = useEpisodeBlacklist();
  const { mutateAsync } = useEpisodeDeleteBlacklist();

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
            promise={() => mutateAsync({ all: true })}
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
