import {
  useEpisodeAddBlacklist,
  useEpisodeHistory,
  useMovieAddBlacklist,
  useMovieHistory,
} from "@/apis/hooks";
import { useModal, usePayload, withModal } from "@/modules/modals";
import { Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { PageTable } from "..";
import QueryOverlay from "../async/QueryOverlay";
import { HistoryIcon } from "../bazarr";
import Language from "../bazarr/Language";
import { BlacklistButton } from "../inputs/blacklist";
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
        className: "text-center",
        Cell: (row) => {
          return <HistoryIcon action={row.value}></HistoryIcon>;
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
        Cell: ({ row }) => {
          const { radarrId } = row.original;
          const { mutateAsync } = useMovieAddBlacklist();
          return (
            <BlacklistButton
              update={history.refetch}
              promise={(form) => mutateAsync({ id: radarrId, form })}
              history={row.original}
            ></BlacklistButton>
          );
        },
      },
    ],
    [history.refetch]
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
        className: "text-center",
        Cell: (row) => {
          return <HistoryIcon action={row.value}></HistoryIcon>;
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
        Cell: ({ row }) => {
          const original = row.original;

          const { sonarrEpisodeId, sonarrSeriesId } = original;
          const { mutateAsync } = useEpisodeAddBlacklist();
          return (
            <BlacklistButton
              history={original}
              promise={(form) =>
                mutateAsync({
                  seriesId: sonarrSeriesId,
                  episodeId: sonarrEpisodeId,
                  form,
                })
              }
            ></BlacklistButton>
          );
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
