import {
  useEpisodeAddBlacklist,
  useEpisodeHistory,
  useMovieAddBlacklist,
  useMovieHistory,
} from "@/apis/hooks";
import { useModal, usePayload, withModal } from "@/modules/modals";
import { faFileExcel } from "@fortawesome/free-solid-svg-icons";
import { Center, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { PageTable } from "..";
import MutateAction from "../async/MutateAction";
import QueryOverlay from "../async/QueryOverlay";
import { HistoryIcon } from "../bazarr";
import Language from "../bazarr/Language";
import TextPopover from "../TextPopover";

const MovieHistoryView: FunctionComponent = () => {
  const movie = usePayload<Item.Movie>();

  const Modal = useModal({ size: "lg" });

  const history = useMovieHistory(movie?.radarrId);

  const { data } = history;

  const columns = useMemo<Column<History.Movie>[]>(
    () => [
      {
        accessor: "action",
        Cell: (row) => (
          <Center>
            <HistoryIcon action={row.value}></HistoryIcon>
          </Center>
        ),
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
        Header: "Score",
        accessor: "score",
      },
      {
        Header: "Date",
        accessor: "timestamp",
        Cell: ({ value, row }) => {
          return (
            <TextPopover text={row.original.parsed_timestamp}>
              <Text>{value}</Text>
            </TextPopover>
          );
        },
      },
      {
        // Actions
        accessor: "blacklisted",
        Cell: ({ row, value }) => {
          const add = useMovieAddBlacklist();
          const { radarrId, provider, subs_id, language, subtitles_path } =
            row.original;

          if (subs_id && provider && language) {
            return (
              <MutateAction
                disabled={value}
                icon={faFileExcel}
                mutation={add}
                args={() => ({
                  id: radarrId,
                  form: {
                    provider,
                    subs_id,
                    subtitles_path,
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
    []
  );

  return (
    <Modal title={`History - ${movie?.title ?? ""}`}>
      <QueryOverlay result={history}>
        <PageTable
          emptyText="No History Found"
          columns={columns}
          data={data ?? []}
        ></PageTable>
      </QueryOverlay>
    </Modal>
  );
};

export const MovieHistoryModal = withModal(MovieHistoryView, "movie-history");

const EpisodeHistoryView: FunctionComponent = () => {
  const episode = usePayload<Item.Episode>();

  const Modal = useModal({ size: "lg" });

  const history = useEpisodeHistory(episode?.sonarrEpisodeId);

  const { data } = history;

  const columns = useMemo<Column<History.Episode>[]>(
    () => [
      {
        accessor: "action",
        Cell: (row) => (
          <Center>
            <HistoryIcon action={row.value}></HistoryIcon>
          </Center>
        ),
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
        Header: "Score",
        accessor: "score",
      },
      {
        Header: "Date",
        accessor: "timestamp",
        Cell: ({ row, value }) => {
          return (
            <TextPopover text={row.original.parsed_timestamp}>
              <Text>{value}</Text>
            </TextPopover>
          );
        },
      },
      {
        // Actions
        accessor: "blacklisted",
        Cell: ({ row, value }) => {
          const {
            sonarrEpisodeId,
            sonarrSeriesId,
            provider,
            subs_id,
            language,
            subtitles_path,
          } = row.original;
          const add = useEpisodeAddBlacklist();

          if (subs_id && provider && language) {
            return (
              <MutateAction
                disabled={value}
                icon={faFileExcel}
                mutation={add}
                args={() => ({
                  seriesId: sonarrSeriesId,
                  episodeId: sonarrEpisodeId,
                  form: {
                    provider,
                    subs_id,
                    subtitles_path,
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
    []
  );

  return (
    <Modal title={`History - ${episode?.title ?? ""}`}>
      <QueryOverlay result={history}>
        <PageTable
          emptyText="No History Found"
          columns={columns}
          data={data ?? []}
        ></PageTable>
      </QueryOverlay>
    </Modal>
  );
};

export const EpisodeHistoryModal = withModal(
  EpisodeHistoryView,
  "episode-history"
);
