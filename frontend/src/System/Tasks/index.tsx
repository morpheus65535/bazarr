import { faSync } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSystemTasks } from "../../apis";
import { ContentHeader, QueryOverlay } from "../../components";
import Table from "./table";

interface Props {}

const SystemTasksView: FunctionComponent<Props> = () => {
  const tasks = useSystemTasks();

  return (
    <QueryOverlay {...tasks}>
      {({ data, isFetching, refetch }) => (
        <Container fluid>
          <Helmet>
            <title>Tasks - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={isFetching}
              icon={faSync}
              onClick={() => refetch()}
            >
              Refresh
            </ContentHeader.Button>
          </ContentHeader>
          <Row>
            <Table tasks={data ?? []}></Table>
          </Row>
        </Container>
      )}
    </QueryOverlay>
  );
};

export default SystemTasksView;
