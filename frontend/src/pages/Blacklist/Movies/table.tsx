import { useMovieDeleteBlacklist } from "@/apis/hooks";
import { PageTable } from "@/components";
import MutateAction from "@/components/async/MutateAction";
import Language from "@/components/bazarr/Language";
import TextPopover from "@/components/TextPopover";
import { useTableStyles } from "@/styles";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { Anchor, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";

interface Props {
  blacklist: readonly Blacklist.Movie[];
}

const Table: FunctionComponent<Props> = ({ blacklist }) => {
  const columns = useMemo<Column<Blacklist.Movie>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
        Cell: (row) => {
          const target = `/movies/${row.row.original.radarrId}`;
          const { classes } = useTableStyles();
          return (
            <Anchor className={classes.primary} component={Link} to={target}>
              {row.value}
            </Anchor>
          );
        },
      },
      {
        Header: "Language",
        accessor: "language",
        Cell: ({ value }) => {
          if (value) {
            return <Language.Text value={value} long></Language.Text>;
          } else {
            return null;
          }
        },
      },
      {
        Header: "Provider",
        accessor: "provider",
      },
      {
        Header: "Date",
        accessor: "timestamp",
        Cell: (row) => {
          if (row.value) {
            return (
              <TextPopover text={row.row.original.parsed_timestamp}>
                <Text>{row.value}</Text>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        accessor: "subs_id",
        Cell: ({ row, value }) => {
          const remove = useMovieDeleteBlacklist();

          return (
            <MutateAction
              label="Remove from Blacklist"
              noReset
              icon={faTrash}
              mutation={remove}
              args={() => ({
                all: false,
                form: {
                  provider: row.original.provider,
                  // eslint-disable-next-line camelcase
                  subs_id: value,
                },
              })}
            ></MutateAction>
          );
        },
      },
    ],
    []
  );
  return (
    <PageTable
      tableStyles={{ emptyText: "No blacklisted movies subtitles" }}
      columns={columns}
      data={blacklist}
    ></PageTable>
  );
};

export default Table;
