import { FunctionComponent, useMemo } from "react";
import { Anchor, Text } from "@mantine/core";
import { faHistory, faTrash } from "@fortawesome/free-solid-svg-icons";
import { ColumnDef } from "@tanstack/react-table";
import { useDeleteBackups, useRestoreBackups } from "@/apis/hooks";
import { Action } from "@/components";
import PageTable from "@/components/tables/PageTable";
import { useModals } from "@/modules/modals";
import { Environment } from "@/utilities";

interface Props {
  backups: System.Backups[];
}

const Table: FunctionComponent<Props> = ({ backups }) => {
  const modals = useModals();

  const restore = useRestoreBackups();

  const remove = useDeleteBackups();

  const columns = useMemo<ColumnDef<System.Backups>[]>(
    () => [
      {
        header: "Name",
        accessorKey: "filename",
        cell: ({
          row: {
            original: { filename },
          },
        }) => {
          return (
            <Anchor
              href={`${Environment.baseUrl}/system/backup/download/${filename}`}
            >
              {filename}
            </Anchor>
          );
        },
      },
      {
        header: "Size",
        accessorKey: "size",
        cell: ({
          row: {
            original: { size },
          },
        }) => {
          return <Text className="table-no-wrap">{size}</Text>;
        },
      },
      {
        header: "Time",
        accessorKey: "date",
        cell: ({
          row: {
            original: { date },
          },
        }) => {
          return <Text className="table-no-wrap">{date}</Text>;
        },
      },
      {
        id: "restore",
        header: "Restore",
        accessorKey: "filename",
        cell: ({
          row: {
            original: { filename },
          },
        }) => {
          return (
            <Action
              label="Restore"
              onClick={() =>
                modals.openConfirmModal({
                  title: "Restore Backup",
                  children: (
                    <Text size="sm">
                      Are you sure you want to restore the backup ({filename})?
                      Bazarr will automatically restart and reload the UI during
                      the restore process.
                    </Text>
                  ),
                  labels: { confirm: "Restore", cancel: "Cancel" },
                  confirmProps: { color: "red" },
                  onConfirm: () => restore.mutate(filename),
                })
              }
              icon={faHistory}
            ></Action>
          );
        },
      },
      {
        id: "delete",
        header: "Delete",
        accessorKey: "filename",
        cell: ({
          row: {
            original: { filename },
          },
        }) => {
          return (
            <Action
              label="Delete"
              c="red"
              onClick={() =>
                modals.openConfirmModal({
                  title: "Delete Backup",
                  children: (
                    <Text size="sm">
                      Are you sure you want to delete the backup ({filename})?
                    </Text>
                  ),
                  labels: { confirm: "Delete", cancel: "Cancel" },
                  confirmProps: { color: "red" },
                  onConfirm: () => remove.mutate(filename),
                })
              }
              icon={faTrash}
            ></Action>
          );
        },
      },
    ],
    [modals, remove, restore],
  );

  return <PageTable columns={columns} data={backups}></PageTable>;
};

export default Table;
