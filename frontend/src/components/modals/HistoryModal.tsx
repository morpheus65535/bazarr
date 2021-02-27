import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Column } from "react-table";
import { AsyncStateOverlay, BaseTable, HistoryIcon } from "..";
import { EpisodesApi, MoviesApi } from "../../apis";
import { updateAsyncState } from "../../utilites";
import { MoviesBlacklistButton, SeriesBlacklistButton } from "../speical";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { usePayload } from "./provider";

export const MovieHistoryModal: FunctionComponent<BaseModalProps> = (props) => {
  const { ...modal } = props;

  const movie = usePayload<Movie>(modal.modalKey);

  const [history, setHistory] = useState<AsyncState<MovieHistory[]>>({
    updating: false,
    items: [],
  });

  const update = useCallback(() => {
    if (movie) {
      updateAsyncState(MoviesApi.history(movie.radarrId), setHistory, []);
    }
  }, [movie]);

  useEffect(() => {
    update();
  }, [update]);

  const columns = useMemo<Column<MovieHistory>[]>(
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
        accessor: (d) => d.language?.name ?? "",
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
      },
      {
        // Actions
        accessor: "subs_id",
        Cell: (row) => {
          const original = row.row.original;
          return (
            <MoviesBlacklistButton
              update={update}
              {...original}
            ></MoviesBlacklistButton>
          );
        },
      },
    ],
    [update]
  );

  return (
    <BaseModal title={`History - ${movie?.title ?? ""}`} {...modal}>
      <AsyncStateOverlay state={history}>
        {(data) => (
          <BaseTable
            emptyText="No History Found"
            columns={columns}
            data={data}
          ></BaseTable>
        )}
      </AsyncStateOverlay>
    </BaseModal>
  );
};

interface EpisodeHistoryProps {}

export const EpisodeHistoryModal: FunctionComponent<
  BaseModalProps & EpisodeHistoryProps
> = (props) => {
  const episode = usePayload<Episode>(props.modalKey);

  const [history, setHistory] = useState<AsyncState<EpisodeHistory[]>>({
    updating: false,
    items: [],
  });

  const update = useCallback(() => {
    if (episode) {
      updateAsyncState(
        EpisodesApi.history(episode.sonarrEpisodeId),
        setHistory,
        []
      );
    }
  }, [episode]);

  useEffect(() => update(), [update]);

  const columns = useMemo<Column<EpisodeHistory>[]>(
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
        accessor: (d) => d.language?.name ?? "",
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
      },
      {
        // Actions
        accessor: "subs_id",
        Cell: (row) => {
          const original = row.row.original;
          return (
            <SeriesBlacklistButton
              seriesid={original.sonarrSeriesId}
              episodeid={original.sonarrEpisodeId}
              path={original.video_path}
              update={update}
              {...original}
            ></SeriesBlacklistButton>
          );
        },
      },
    ],
    [update]
  );

  return (
    <BaseModal title={`History - ${episode?.title ?? ""}`} {...props}>
      <AsyncStateOverlay state={history}>
        {(data) => (
          <BaseTable
            emptyText="No History Found"
            columns={columns}
            data={data}
          ></BaseTable>
        )}
      </AsyncStateOverlay>
    </BaseModal>
  );
};
