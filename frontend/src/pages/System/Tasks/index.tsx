import { FunctionComponent } from "react";
import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faSync } from "@fortawesome/free-solid-svg-icons";
import { useSystemTasks } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import Table from "./table";

const SystemTasksView: FunctionComponent = () => {
  const tasks = useSystemTasks();

  const { isFetching, data, refetch } = tasks;

  useDocumentTitle("Tasks - Bazarr (System)");

  return (
    <QueryOverlay result={tasks}>
      <Container fluid px={0}>
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
