import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router";
import { Anchor, Text } from "@mantine/core";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { ColumnDef } from "@tanstack/react-table";
import { useMovieDeleteBlacklist } from "@/apis/hooks";
import MutateAction from "@/components/async/MutateAction";
import Language from "@/components/bazarr/Language";
import PageTable from "@/components/tables/PageTable";
import TextPopover from "@/components/TextPopover";

interface Props {
  blacklist: Blacklist.Movie[];
}

const Table: FunctionComponent<Props> = ({ blacklist }) => {
  const remove = useMovieDeleteBlacklist();

  const columns = useMemo<ColumnDef<Blacklist.Movie>[]>(
    () => [
      {
        header: "Name",
        accessorKey: "title",
        cell: ({
          row: {
            original: { radarrId },
          },
        }) => {
          const target = `/movies/${radarrId}`;
          return (
            <Anchor className="table-primary" component={Link} to={target}>
              {radarrId}
            </Anchor>
          );
        },
      },
      {
        header: "Language",
        accessorKey: "language",
        cell: ({
          row: {
            original: { language },
          },
        }) => {
          if (language) {
            return <Language.Text value={language} long></Language.Text>;
          } else {
            return null;
          }
        },
      },
      {
        header: "Provider",
        accessorKey: "provider",
      },
      {
        header: "Date",
        accessorKey: "timestamp",
        cell: ({
          row: {
            original: { timestamp, parsed_timestamp: parsedTimestamp },
          },
        }) => {
          if (timestamp) {
            return (
              <TextPopover text={parsedTimestamp}>
                <Text>{timestamp}</Text>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        id: "subs_id",
        cell: ({
          row: {
            original: { subs_id: subsId, provider },
          },
        }) => {
          return (
            <MutateAction
              label="Remove from Blacklist"
              icon={faTrash}
              mutation={remove}
              args={() => ({
                all: false,
                form: {
                  provider: provider,
                  // eslint-disable-next-line camelcase
                  subs_id: subsId,
                },
              })}
            ></MutateAction>
          );
        },
      },
    ],
    [remove],
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
