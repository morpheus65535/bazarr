import { useRunTask } from "@/apis/hooks";
import { SimpleTable } from "@/components";
import MutateAction from "@/components/async/MutateAction";
import { useTableStyles } from "@/styles";
import { faPlay } from "@fortawesome/free-solid-svg-icons";
import { Text } from "@mantine/core";
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
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.primary}>{value}</Text>;
        },
      },
      {
        Header: "Interval",
        accessor: "interval",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.noWrap}>{value}</Text>;
        },
      },
      {
        Header: "Next Execution",
        accessor: "next_run_in",
      },
      {
        accessor: "job_running",
        Cell: ({ row, value }) => {
          const { job_id } = row.original;
          const runTask = useRunTask();

          return (
            <MutateAction
              label="Run"
              icon={faPlay}
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
