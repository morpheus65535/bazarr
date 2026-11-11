import { FunctionComponent, useMemo } from "react";
import { Badge, Text } from "@mantine/core";
import { faFileExcel, faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  useSportsAddBlacklist,
  useSportsHistoryPagination,
} from "@/apis/hooks";
import { MutateAction } from "@/components/async";
import { HistoryIcon } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import StateIcon from "@/components/StateIcon";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import TextPopover from "@/components/TextPopover";
import HistoryView from "@/pages/views/HistoryView";

const SportsHistoryView: FunctionComponent = () => {
  const addToBlacklist = useSportsAddBlacklist();

  const columns = useMemo<ColumnDef<History.SportsEvent>[]>(
    () => [
      {
        id: "action",
        cell: ({ row: { original } }) => (
          <HistoryIcon action={original.action}></HistoryIcon>
        ),
      },
      {
        header: "League",
        accessorKey: "leagueTitle",
      },
      {
        header: "Event",
        accessorKey: "eventTitle",
        cell: ({
          row: {
            original: { eventTitle },
          },
        }) => {
          return <Text className="table-no-wrap">{eventTitle}</Text>;
        },
      },
      {
        // The part names which file of the event this row covers. Most events
        // have one file and no part name.
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
            return (
              <Badge color="secondary">
                <Language.Text value={language} long></Language.Text>
              </Badge>
            );
          } else {
            return null;
          }
        },
      },
      {
        header: "Score",
        accessorKey: "score",
      },
      {
        header: "Match",
        accessorKey: "matches",
        cell: (row) => {
          const { matches, dontMatches: dont } = row.row.original;
          if (matches.length || dont.length) {
            return (
              <StateIcon
                matches={matches}
                dont={dont}
                isHistory={true}
              ></StateIcon>
            );
          } else {
            return null;
          }
        },
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
        header: "Info",
        accessorKey: "description",
        cell: ({
          row: {
            original: { description },
          },
        }) => {
          return (
            <TextPopover text={description}>
              <FontAwesomeIcon size="sm" icon={faInfoCircle}></FontAwesomeIcon>
            </TextPopover>
          );
        },
      },
      {
        header: "Blacklist",
        accessorKey: "blacklisted",
        cell: ({ row }) => {
          const {
            sportsEventId,
            sportarrLeagueId,
            provider,
            subsId,
            language,
            subtitlesPath,
            blacklisted,
          } = row.original;
          if (subsId && provider && language) {
            return (
              <MutateAction
                label="Add to Blacklist"
                disabled={blacklisted}
                icon={faFileExcel}
                mutation={addToBlacklist}
                args={() => ({
                  leagueId: sportarrLeagueId,
                  eventId: sportsEventId,
                  form: {
                    provider,
                    subsId,
                    subtitlesPath,
                    language: language.code2,
                  },
                })}
              ></MutateAction>
            );
          } else {
            return null;
          }
        },
      },
    ],
    [addToBlacklist],
  );

  const query = useSportsHistoryPagination();

  return (
    <HistoryView name="Sports" query={query} columns={columns}></HistoryView>
  );
};

export default SportsHistoryView;
