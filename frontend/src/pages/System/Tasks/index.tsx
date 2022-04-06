import { useSystemTasks } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { faSync } from "@fortawesome/free-solid-svg-icons";
import { Container } from "@mantine/core";
import { FunctionComponent } from "react";
import { Helmet } from "react-helmet";
import Table from "./table";

const SystemTasksView: FunctionComponent = () => {
  const tasks = useSystemTasks();

  const { isFetching, data, refetch } = tasks;

  return (
    <QueryOverlay result={tasks}>
      <Container fluid px={0}>
        <Helmet>
          <title>Tasks - Bazarr (System)</title>
        </Helmet>
        <Toolbox>
          <Toolbox.Button
            loading={isFetching}
            icon={faSync}
            onClick={() => refetch()}
          >
            Refresh
          </Toolbox.Button>
        </Toolbox>
        <Table tasks={data ?? []}></Table>
      </Container>
    </QueryOverlay>
  );
};

export default SystemTasksView;
