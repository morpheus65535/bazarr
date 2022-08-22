import { useDeleteBackups, useRestoreBackups } from "@/apis/hooks";
import { Action, PageTable } from "@/components";
import { useModals } from "@/modules/modals";
import { useTableStyles } from "@/styles";
import { Environment } from "@/utilities";
import { faClock, faHistory, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Anchor, Group, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";

interface Props {
  backups: readonly System.Backups[];
}

const Table: FunctionComponent<Props> = ({ backups }) => {
  const columns: Column<System.Backups>[] = useMemo<Column<System.Backups>[]>(
    () => [
      {
        accessor: "type",
        Cell: <FontAwesomeIcon icon={faClock}></FontAwesomeIcon>,
      },
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
          const { classes } = useTableStyles();
          return <Text className={classes.noWrap}>{value}</Text>;
        },
      },
      {
        Header: "Time",
        accessor: "date",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.noWrap}>{value}</Text>;
        },
      },
      {
        id: "actions",
        accessor: "filename",
        Cell: ({ value }) => {
          const modals = useModals();
          const restore = useRestoreBackups();
          const remove = useDeleteBackups();
          return (
            <Group spacing="xs" noWrap>
              <Action
                label="Restore"
                onClick={() =>
                  modals.openConfirmModal({
                    title: "Restore Backup",
                    children: (
                      <Text size="sm">
                        Are you sure you want to restore the backup ({value})?
                        Bazarr will automatically restart and reload the UI
                        during the restore process.
                      </Text>
                    ),
                    labels: { confirm: "Restore", cancel: "Cancel" },
                    confirmProps: { color: "red" },
                    onConfirm: () => restore.mutate(value),
                  })
                }
                icon={faHistory}
              ></Action>
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
            </Group>
          );
        },
      },
    ],
    []
  );

  return <PageTable columns={columns} data={backups}></PageTable>;
};

export default Table;
