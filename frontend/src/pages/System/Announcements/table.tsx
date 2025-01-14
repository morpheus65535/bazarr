import { FunctionComponent, JSX, useMemo } from "react";
import { Anchor, Text } from "@mantine/core";
import { faWindowClose } from "@fortawesome/free-solid-svg-icons";
import { ColumnDef } from "@tanstack/react-table";
import { useSystemAnnouncementsAddDismiss } from "@/apis/hooks";
import { MutateAction } from "@/components/async";
import SimpleTable from "@/components/tables/SimpleTable";

interface Props {
  announcements: System.Announcements[];
}

const Table: FunctionComponent<Props> = ({ announcements }) => {
  const addDismiss = useSystemAnnouncementsAddDismiss();

  const columns: ColumnDef<System.Announcements>[] = useMemo<
    ColumnDef<System.Announcements>[]
  >(
    () => [
      {
        header: "Since",
        accessorKey: "timestamp",
        cell: ({
          row: {
            original: { timestamp },
          },
        }) => {
          return <Text className="table-primary">{timestamp}</Text>;
        },
      },
      {
        header: "Announcement",
        accessorKey: "text",
        cell: ({
          row: {
            original: { text },
          },
        }) => {
          return <Text className="table-primary">{text}</Text>;
        },
      },
      {
        header: "More Info",
        accessorKey: "link",
        cell: ({
          row: {
            original: { link },
          },
        }) => {
          if (link) {
            return <Label link={link}>Link</Label>;
          } else {
            return <Text>n/a</Text>;
          }
        },
      },
      {
        header: "Dismiss",
        accessorKey: "hash",
        cell: ({
          row: {
            original: { dismissible, hash },
          },
        }) => {
          return (
            <MutateAction
              label="Dismiss announcement"
              disabled={!dismissible}
              icon={faWindowClose}
              mutation={addDismiss}
              args={() => ({
                hash: hash,
              })}
            ></MutateAction>
          );
        },
      },
    ],
    [addDismiss],
  );

  return (
    <SimpleTable
      columns={columns}
      data={announcements}
      tableStyles={{ emptyText: "No announcements for now, come back later!" }}
    ></SimpleTable>
  );
};

export default Table;

interface LabelProps {
  link: string;
  children: string;
}

function Label(props: LabelProps): JSX.Element {
  const { link, children } = props;
  return (
    <Anchor href={link} target="_blank" rel="noopener noreferrer">
      {children}
    </Anchor>
  );
}
