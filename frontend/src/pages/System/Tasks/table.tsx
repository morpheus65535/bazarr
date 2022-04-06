import { useRunTask } from "@/apis/hooks";
import { SimpleTable } from "@/components";
import MutateAction from "@/components/async/MutateAction";
import { faSync } from "@fortawesome/free-solid-svg-icons";
import { FunctionComponent, useMemo } from "react";
import { Column, useSortBy } from "react-table";

interface Props {
  tasks: readonly System.Task[];
}

const Table: FunctionComponent<Props> = ({ tasks }) => {
  const columns: Column<System.Task>[] = useMemo<Column<System.Task>[]>(
    () => [
      {
        Header: "Name",
        accessor: "name",
        className: "text-nowrap",
      },
      {
        Header: "Interval",
        accessor: "interval",
        className: "text-nowrap",
      },
      {
        Header: "Next Execution",
        accessor: "next_run_in",
        className: "text-nowrap",
      },
      {
        accessor: "job_running",
        Cell: ({ row, value }) => {
          const { job_id } = row.original;
          const runTask = useRunTask();

          return (
            <MutateAction
              icon={faSync}
              iconProps={{ spin: value }}
              mutation={runTask}
              args={() => job_id}
            ></MutateAction>
          );
        },
      },
    ],
    []
  );

  return (
    <SimpleTable
      initialState={{ sortBy: [{ id: "name", desc: false }] }}
      columns={columns}
      data={tasks}
      plugins={[useSortBy]}
    ></SimpleTable>
  );
};

export default Table;
