import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router";
import { Anchor, Text } from "@mantine/core";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { ColumnDef } from "@tanstack/react-table";
import { useEpisodeDeleteBlacklist } from "@/apis/hooks";
import MutateAction from "@/components/async/MutateAction";
import Language from "@/components/bazarr/Language";
import PageTable from "@/components/tables/PageTable";
import TextPopover from "@/components/TextPopover";

interface Props {
  blacklist: Blacklist.Episode[];
}

const Table: FunctionComponent<Props> = ({ blacklist }) => {
  const removeFromBlacklist = useEpisodeDeleteBlacklist();

  const columns = useMemo<ColumnDef<Blacklist.Episode>[]>(
    () => [
      {
        header: "Series",
        accessorKey: "seriesTitle",
        cell: ({
          row: {
            original: { sonarrSeriesId, seriesTitle },
          },
        }) => {
          const target = `/series/${sonarrSeriesId}`;
          return (
            <Anchor className="table-primary" component={Link} to={target}>
              {seriesTitle}
            </Anchor>
          );
        },
      },
      {
        header: "Episode",
        accessorKey: "episode_number",
      },
      {
        id: "episodeTitle",
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
              mutation={removeFromBlacklist}
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
    [removeFromBlacklist],
  );
  return (
    <PageTable
      tableStyles={{ emptyText: "No blacklisted series subtitles" }}
      columns={columns}
      data={blacklist}
    ></PageTable>
  );
};

export default Table;
