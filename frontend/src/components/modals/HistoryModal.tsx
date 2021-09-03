import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";
import { useDidUpdate } from "rooks";
import { HistoryIcon, LanguageText, PageTable, TextPopover } from "..";
import { EpisodesApi, MoviesApi, useAsyncRequest } from "../../apis";
import { BlacklistButton } from "../../DisplayItem/generic/blacklist";
import { AsyncOverlay } from "../async";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useModalPayload } from "./hooks";

export const MovieHistoryModal: FunctionComponent<BaseModalProps> = (props) => {
  const { ...modal } = props;

  const movie = useModalPayload<Item.Movie>(modal.modalKey);

  const [history, updateHistory] = useAsyncRequest(
    MoviesApi.historyBy.bind(MoviesApi)
  );

  const update = useCallback(() => {
    if (movie) {
      updateHistory(movie.movieId);
    }
  }, [movie, updateHistory]);

  useDidUpdate(() => {
    update();
  }, [movie?.movieId]);

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
            return <LanguageText text={value} long></LanguageText>;
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
        Cell: (row) => {
          if (row.value) {
            return (
              <TextPopover text={row.row.original.parsed_timestamp} delay={1}>
                <span>{row.value}</span>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        // Actions
        accessor: "blacklisted",
        Cell: ({ row }) => {
          const original = row.original;
          return (
            <BlacklistButton
              update={update}
              promise={(form) => MoviesApi.addBlacklist(original.movieId, form)}
              history={original}
            ></BlacklistButton>
          );
        },
      },
    ],
    [update]
  );

  return (
    <BaseModal title={`History - ${movie?.title ?? ""}`} {...modal}>
      <AsyncOverlay ctx={history}>
        {({ content }) => (
          <PageTable
            emptyText="No History Found"
            columns={columns}
            data={content?.data ?? []}
          ></PageTable>
        )}
      </AsyncOverlay>
    </BaseModal>
  );
};

interface EpisodeHistoryProps {}

export const EpisodeHistoryModal: FunctionComponent<
  BaseModalProps & EpisodeHistoryProps
> = (props) => {
  const episode = useModalPayload<Item.Episode>(props.modalKey);

  const [history, updateHistory] = useAsyncRequest(
    EpisodesApi.historyBy.bind(EpisodesApi)
  );

  const update = useCallback(() => {
    if (episode) {
      updateHistory(episode.episodeId);
    }
  }, [episode, updateHistory]);

  useDidUpdate(() => {
    update();
  }, [episode?.episodeId]);

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
            return <LanguageText text={value} long></LanguageText>;
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
        Cell: (row) => {
          if (row.value) {
            return (
              <TextPopover text={row.row.original.parsed_timestamp} delay={1}>
                <span>{row.value}</span>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        // Actions
        accessor: "blacklisted",
        Cell: ({ row }) => {
          const original = row.original;
          const { seriesId, episodeId } = original;
          return (
            <BlacklistButton
              history={original}
              update={update}
              promise={(form) =>
                EpisodesApi.addBlacklist(seriesId, episodeId, form)
              }
            ></BlacklistButton>
          );
        },
      },
    ],
    [update]
  );

  return (
    <BaseModal title={`History - ${episode?.title ?? ""}`} {...props}>
      <AsyncOverlay ctx={history}>
        {({ content }) => (
          <PageTable
            emptyText="No History Found"
            columns={columns}
            data={content?.data ?? []}
          ></PageTable>
        )}
      </AsyncOverlay>
    </BaseModal>
  );
};
