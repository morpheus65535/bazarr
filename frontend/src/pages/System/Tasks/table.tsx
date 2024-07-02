import { FunctionComponent, useMemo } from "react";
import { Text } from "@mantine/core";
import { faPlay } from "@fortawesome/free-solid-svg-icons";
import { ColumnDef, getSortedRowModel } from "@tanstack/react-table";
import { useRunTask } from "@/apis/hooks";
import MutateAction from "@/components/async/MutateAction";
import NewSimpleTable from "@/components/tables/NewSimpleTable";

interface Props {
  tasks: System.Task[];
}

const Table: FunctionComponent<Props> = ({ tasks }) => {
  const runTask = useRunTask();

  const columns: ColumnDef<System.Task>[] = useMemo<ColumnDef<System.Task>[]>(
    () => [
      {
        header: "Name",
        accessor: "name",
        cell: ({
          row: {
            original: { name },
          },
        }) => {
          return <Text className="table-primary">{name}</Text>;
        },
      },
      {
        header: "Interval",
        accessor: "interval",
        cell: ({
          row: {
            original: { interval },
          },
        }) => {
          return <Text className="table-no-wrap">{interval}</Text>;
        },
      },
      {
        header: "Next Execution",
        accessor: "next_run_in",
      },
      {
        header: "Run",
        accessor: "job_running",
        cell: ({
          row: {
            original: { job_id: jobId, job_running: jobRunning },
          },
        }) => {
          return (
            <MutateAction
              label="Run Job"
              icon={faPlay}
              iconProps={{ spin: jobRunning }}
              mutation={runTask}
              args={() => jobId}
            ></MutateAction>
          );
        },
      },
    ],
    [runTask],
  );

  return (
    <NewSimpleTable
      initialState={{ sorting: [{ id: "name", desc: false }] }}
      columns={columns}
      data={tasks}
      enableSorting
      getSortedRowModel={getSortedRowModel()}
    ></NewSimpleTable>
  );
};

export default Table;
