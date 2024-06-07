import { useDeleteBackups, useRestoreBackups } from "@/apis/hooks";
import { Action, PageTable } from "@/components";
import { useModals } from "@/modules/modals";
import { Environment } from "@/utilities";
import { faHistory, faTrash } from "@fortawesome/free-solid-svg-icons";
import { Anchor, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";

interface Props {
  backups: readonly System.Backups[];
}

const Table: FunctionComponent<Props> = ({ backups }) => {
  const columns: Column<System.Backups>[] = useMemo<Column<System.Backups>[]>(
    () => [
      {
        Header: "Name",
        accessor: "filename",
        Cell: ({ value }) => {
          return (
            <Anchor
              href={`${Environment.baseUrl}/system/backup/download/${value}`}
            >
              {value}
            </Anchor>
          );
        },
      },
      {
        Header: "Size",
        accessor: "size",
        Cell: ({ value }) => {
          return <Text className="table-no-wrap">{value}</Text>;
        },
      },
      {
        Header: "Time",
        accessor: "date",
        Cell: ({ value }) => {
          return <Text className="table-no-wrap">{value}</Text>;
        },
      },
      {
        id: "restore",
        Header: "Restore",
        accessor: "filename",
        Cell: ({ value }) => {
          const modals = useModals();
          const restore = useRestoreBackups();
          return (
            <Action
              label="Restore"
              onClick={() =>
                modals.openConfirmModal({
                  title: "Restore Backup",
                  children: (
                    <Text size="sm">
                      Are you sure you want to restore the backup ({value})?
                      Bazarr will automatically restart and reload the UI during
                      the restore process.
                    </Text>
                  ),
                  labels: { confirm: "Restore", cancel: "Cancel" },
                  confirmProps: { color: "red" },
                  onConfirm: () => restore.mutate(value),
                })
              }
              icon={faHistory}
            ></Action>
          );
        },
      },
      {
        id: "delet4",
        Header: "Delete",
        accessor: "filename",
        Cell: ({ value }) => {
          const modals = useModals();
          const remove = useDeleteBackups();
          return (
            <Action
              label="Delete"
              color="red"
              onClick={() =>
                modals.openConfirmModal({
                  title: "Delete Backup",
                  children: (
                    <Text size="sm">
                      Are you sure you want to delete the backup ({value})?
                    </Text>
                  ),
                  labels: { confirm: "Delete", cancel: "Cancel" },
                  confirmProps: { color: "red" },
                  onConfirm: () => remove.mutate(value),
                })
              }
              icon={faTrash}
            ></Action>
          );
        },
      },
    ],
    [],
  );

  return <PageTable columns={columns} data={backups}></PageTable>;
};

export default Table;
