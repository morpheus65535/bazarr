import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
} from "react";
import { Column } from "react-table";
import { HistoryIcon, LanguageText, PageTable, TextPopover } from "..";
import { EpisodesApi, MoviesApi, useAsyncRequest } from "../../apis";
import { BlacklistButton } from "../../generic/blacklist";
import { AsyncOverlay } from "../async";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { usePayload } from "./provider";

export const MovieHistoryModal: FunctionComponent<BaseModalProps> = (props) => {
  const { ...modal } = props;

  const movie = usePayload<Item.Movie>(modal.modalKey);

  const [history, setHistory] = useAsyncRequest(
    MoviesApi.history.bind(MoviesApi),
    []
  );

  const update = useCallback(() => {
    if (movie) {
      setHistory(movie.radarrId);
    }
  }, [movie, setHistory]);

  useEffect(() => {
    update();
  }, [update]);

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
              promise={(form) =>
                MoviesApi.addBlacklist(original.radarrId, form)
              }
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
            data={content}
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
  const episode = usePayload<Item.Episode>(props.modalKey);

  const [history, setHistory] = useAsyncRequest(
    EpisodesApi.history.bind(EpisodesApi),
    []
  );

  const update = useCallback(() => {
    if (episode) {
      setHistory(episode.sonarrEpisodeId);
    }
  }, [episode, setHistory]);

  useEffect(() => update(), [update]);

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
          const { sonarrSeriesId, sonarrEpisodeId } = original;
          return (
            <BlacklistButton
              history={original}
              update={update}
              promise={(form) =>
                EpisodesApi.addBlacklist(sonarrSeriesId, sonarrEpisodeId, form)
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
            data={content}
          ></PageTable>
        )}
      </AsyncOverlay>
    </BaseModal>
  );
};
