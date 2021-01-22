import React, { FunctionComponent, useEffect, useMemo, useState } from "react";
import BasicModal, { ModalProps } from "./BasicModal";
import { Column } from "react-table";
import { BasicTable, HistoryIcon, AsyncStateOverlay } from "..";

import { updateAsyncState } from "../../utilites";
import { MoviesApi, EpisodesApi } from "../../apis";

interface MovieHistoryProps {
  movie: Movie;
}

export const MovieHistoryModal: FunctionComponent<
  ModalProps & MovieHistoryProps
> = (props) => {
  const { movie, ...modal } = props;

  const [history, setHistory] = useState<AsyncState<MovieHistory[]>>({
    updating: false,
    items: [],
  });

  useEffect(() => {
    if (modal.show) {
      updateAsyncState(MoviesApi.history(movie.radarrId), setHistory, []);
    }
  }, [movie, modal.show]);

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
        accessor: (d) => d.language.name,
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
        accessor: "radarrId",
        Cell: (row) => {
          return null;
        },
      },
    ],
    []
  );

  return (
    <BasicModal title={`History - ${movie.title}`} {...modal}>
      <AsyncStateOverlay state={history}>
        {(data) => (
          <BasicTable
            emptyText="No History Found"
            options={{ columns, data }}
          ></BasicTable>
        )}
      </AsyncStateOverlay>
    </BasicModal>
  );
};

interface EpisodeHistoryProps {
  episode?: Episode;
}

export const EpisodeHistoryModal: FunctionComponent<
  ModalProps & EpisodeHistoryProps
> = (props) => {
  const { episode } = props;
  const [history, setHistory] = useState<AsyncState<EpisodeHistory[]>>({
    updating: false,
    items: [],
  });

  useEffect(() => {
    if (episode) {
      updateAsyncState(
        EpisodesApi.history(episode.sonarrEpisodeId),
        setHistory,
        []
      );
    }
  }, [episode]);

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
        accessor: (d) => d.language.name,
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
        accessor: "sonarrEpisodeId",
        Cell: (row) => {
          return null;
        },
      },
    ],
    []
  );

  return (
    <BasicModal title={`History - ${episode?.title ?? ""}`} {...props}>
      <AsyncStateOverlay state={history}>
        {(data) => (
          <BasicTable
            emptyText="No History Found"
            options={{ columns, data }}
          ></BasicTable>
        )}
      </AsyncStateOverlay>
    </BasicModal>
  );
};
