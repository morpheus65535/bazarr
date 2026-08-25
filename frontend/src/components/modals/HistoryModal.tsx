import { FunctionComponent, useMemo } from "react";
import { Badge, Center, Text } from "@mantine/core";
import { faFileExcel, faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  useEpisodeAddBlacklist,
  useEpisodeHistory,
  useMovieAddBlacklist,
  useMovieHistory,
  useSportsAddBlacklist,
  useSportsHistory,
} from "@/apis/hooks";
import MutateAction from "@/components/async/MutateAction";
import QueryOverlay from "@/components/async/QueryOverlay";
import { HistoryIcon } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import StateIcon from "@/components/StateIcon";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import PageTable from "@/components/tables/PageTable";
import TextPopover from "@/components/TextPopover";
import { withModal } from "@/modules/modals";

interface MovieHistoryViewProps {
  movie: Item.Movie;
}

const MovieHistoryView: FunctionComponent<MovieHistoryViewProps> = ({
  movie,
}) => {
  const history = useMovieHistory(movie.radarrId);

  const { data } = history;

  const addMovieToBlacklist = useMovieAddBlacklist();

  const columns = useMemo<ColumnDef<History.Movie>[]>(
    () => [
      {
        id: "action",
        cell: ({
          row: {
            original: { action },
          },
        }) => (
          <Center>
            <HistoryIcon action={action}></HistoryIcon>
          </Center>
        ),
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
              <Badge>
                <Language.Text value={language} long></Language.Text>
              </Badge>
            );
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
        header: "Score",
        accessorKey: "score",
      },
      {
        id: "matches",
        cell: ({
          row: {
            original: { matches, dontMatches: dont },
          },
        }) => {
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
          return (
            <TextPopover text={parsedTimestamp}>
              <Text>{timestamp}</Text>
            </TextPopover>
          );
        },
      },
      {
        // Actions
        id: "blacklisted",
        cell: ({
          row: {
            original: {
              blacklisted,
              radarrId,
              provider,
              subsId,
              language,
              subtitlesPath,
            },
          },
        }) => {
          if (subsId && provider && language) {
            return (
              <MutateAction
                label="Add to Blacklist"
                disabled={blacklisted}
                icon={faFileExcel}
                mutation={addMovieToBlacklist}
                args={() => ({
                  id: radarrId,
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
    [addMovieToBlacklist],
  );

  return (
    <QueryOverlay result={history}>
      <PageTable
        columns={columns}
        data={data ?? []}
        tableStyles={{ emptyText: "No history found" }}
      ></PageTable>
    </QueryOverlay>
  );
};

export const MovieHistoryModal = withModal(MovieHistoryView, "movie-history", {
  size: "xl",
  title: "Movie History",
});

interface EpisodeHistoryViewProps {
  episode: Item.Episode;
}

const EpisodeHistoryView: FunctionComponent<EpisodeHistoryViewProps> = ({
  episode,
}) => {
  const history = useEpisodeHistory(episode.sonarrEpisodeId);

  const { data } = history;

  const addEpisodeToBlacklist = useEpisodeAddBlacklist();

  const columns = useMemo<ColumnDef<History.Episode>[]>(
    () => [
      {
        id: "action",
        cell: ({
          row: {
            original: { action },
          },
        }) => (
          <Center>
            <HistoryIcon action={action}></HistoryIcon>
          </Center>
        ),
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
              <Badge>
                <Language.Text value={language} long></Language.Text>
              </Badge>
            );
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
        header: "Score",
        accessorKey: "score",
      },
      {
        id: "matches",
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
          return (
            <TextPopover text={parsedTimestamp}>
              <Text>{timestamp}</Text>
            </TextPopover>
          );
        },
      },
      {
        id: "description",
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
        // Actions
        id: "blacklisted",
        cell: ({
          row: {
            original: {
              blacklisted,
              sonarrEpisodeId,
              sonarrSeriesId,
              provider,
              subsId,
              language,
              subtitlesPath,
            },
          },
        }) => {
          if (subsId && provider && language) {
            return (
              <MutateAction
                label="Add to Blacklist"
                disabled={blacklisted}
                icon={faFileExcel}
                mutation={addEpisodeToBlacklist}
                args={() => ({
                  seriesId: sonarrSeriesId,
                  episodeId: sonarrEpisodeId,
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
    [addEpisodeToBlacklist],
  );

  return (
    <QueryOverlay result={history}>
      <PageTable
        autoScroll={false}
        tableStyles={{ emptyText: "No history found", placeholder: 5 }}
        columns={columns}
        data={data ?? []}
      ></PageTable>
    </QueryOverlay>
  );
};

export const EpisodeHistoryModal = withModal(
  EpisodeHistoryView,
  "episode-history",
  { size: "xl" },
);

interface SportsEventHistoryViewProps {
  event: Item.SportsEvent;
}

const SportsEventHistoryView: FunctionComponent<
  SportsEventHistoryViewProps
> = ({ event }) => {
  const history = useSportsHistory(event.sportsEventId);

  const { data } = history;

  const addSportsEventToBlacklist = useSportsAddBlacklist();

  const columns = useMemo<ColumnDef<History.SportsEvent>[]>(
    () => [
      {
        id: "action",
        cell: ({
          row: {
            original: { action },
          },
        }) => (
          <Center>
            <HistoryIcon action={action}></HistoryIcon>
          </Center>
        ),
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
              <Badge>
                <Language.Text value={language} long></Language.Text>
              </Badge>
            );
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
        header: "Score",
        accessorKey: "score",
      },
      {
        id: "matches",
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
          return (
            <TextPopover text={parsedTimestamp}>
              <Text>{timestamp}</Text>
            </TextPopover>
          );
        },
      },
      {
        id: "description",
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
        // Actions
        id: "blacklisted",
        cell: ({
          row: {
            original: {
              blacklisted,
              sportsEventId,
              sportarrLeagueId,
              provider,
              subsId,
              language,
              subtitlesPath,
            },
          },
        }) => {
          if (subsId && provider && language) {
            return (
              <MutateAction
                label="Add to Blacklist"
                disabled={blacklisted}
                icon={faFileExcel}
                mutation={addSportsEventToBlacklist}
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
    [addSportsEventToBlacklist],
  );

  return (
    <QueryOverlay result={history}>
      <PageTable
        autoScroll={false}
        tableStyles={{ emptyText: "No history found", placeholder: 5 }}
        columns={columns}
        data={data ?? []}
      ></PageTable>
    </QueryOverlay>
  );
};

export const SportsEventHistoryModal = withModal(
  SportsEventHistoryView,
  "sports-event-history",
  { size: "xl" },
);
