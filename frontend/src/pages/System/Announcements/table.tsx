import { useSystemAnnouncementsAddDismiss } from "@/apis/hooks";
import { SimpleTable } from "@/components";
import { MutateAction } from "@/components/async";
import { useTableStyles } from "@/styles";
import { faWindowClose } from "@fortawesome/free-solid-svg-icons";
import { Anchor, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";

interface Props {
  announcements: readonly System.Announcements[];
}

const Table: FunctionComponent<Props> = ({ announcements }) => {
  const columns: Column<System.Announcements>[] = useMemo<
    Column<System.Announcements>[]
  >(
    () => [
      {
        Header: "Since",
        accessor: "timestamp",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.primary}>{value}</Text>;
        },
      },
      {
        Header: "Announcement",
        accessor: "text",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.primary}>{value}</Text>;
        },
      },
      {
        Header: "More info",
        accessor: "link",
        Cell: ({ value }) => {
          if (value) {
            return <Label link={value}>Link</Label>;
          } else {
            return <Text>n/a</Text>;
          }
        },
      },
      {
        Header: "Dismiss",
        accessor: "hash",
        Cell: ({ row, value }) => {
          const add = useSystemAnnouncementsAddDismiss();
          return (
            <MutateAction
              label="Dismiss announcement"
              disabled={!row.original.dismissible}
              icon={faWindowClose}
              mutation={add}
              args={() => ({
                hash: value,
              })}
            ></MutateAction>
          );
        },
      },
    ],
    []
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
