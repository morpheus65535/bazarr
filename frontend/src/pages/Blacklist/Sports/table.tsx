import { FunctionComponent, useMemo } from "react";
import { Text } from "@mantine/core";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useSportsDeleteBlacklist } from "@/apis/hooks";
import MutateAction from "@/components/async/MutateAction";
import Language from "@/components/bazarr/Language";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import PageTable from "@/components/tables/PageTable";
import TextPopover from "@/components/TextPopover";

interface Props {
  blacklist: Blacklist.SportsEvent[];
}

const Table: FunctionComponent<Props> = ({ blacklist }) => {
  const removeFromBlacklist = useSportsDeleteBlacklist();

  const columns = useMemo<ColumnDef<Blacklist.SportsEvent>[]>(
    () => [
      {
        header: "League",
        accessorKey: "leagueTitle",
      },
      {
        header: "Event",
        accessorKey: "eventTitle",
      },
      {
        header: "Part",
        accessorKey: "partName",
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
            original: { timestamp, parsedTimestamp },
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
        id: "subsId",
        cell: ({
          row: {
            original: { subsId, provider },
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
                  subsId,
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
      tableStyles={{ emptyText: "No blacklisted sports events subtitles" }}
      columns={columns}
      data={blacklist}
    ></PageTable>
  );
};

export default Table;
