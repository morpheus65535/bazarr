import React, { FunctionComponent, useMemo } from "react";
import { useQuery } from "react-query";
import { Column } from "react-table";
import {
  HistoryIcon,
  LanguageText,
  PageTable,
  QueryOverlay,
  TextPopover,
} from "..";
import api from "../../apis/raw";
import { BlacklistButton } from "../../DisplayItem/generic/blacklist";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useModalPayload } from "./hooks";

export const MovieHistoryModal: FunctionComponent<BaseModalProps> = (props) => {
  const { ...modal } = props;

  const movie = useModalPayload<Item.Movie>(modal.modalKey);

  const history = useQuery(["movies", movie?.radarrId], () => {
    if (movie) {
      api.movies.historyBy(movie.radarrId);
    }
  });

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
              update={history.refetch}
              promise={(form) =>
                api.movies.addBlacklist(original.radarrId, form)
              }
              history={original}
            ></BlacklistButton>
          );
        },
      },
    ],
    [history.refetch]
  );

  return (
    <BaseModal title={`History - ${movie?.title ?? ""}`} {...modal}>
      <QueryOverlay result={history}>
        <PageTable
          emptyText="No History Found"
          columns={columns}
          data={data ?? []}
        ></PageTable>
      </QueryOverlay>
    </BaseModal>
  );
};

interface EpisodeHistoryProps {}

export const EpisodeHistoryModal: FunctionComponent<
  BaseModalProps & EpisodeHistoryProps
> = (props) => {
  const episode = useModalPayload<Item.Episode>(props.modalKey);

  const history = useQuery(["episodes", episode?.sonarrEpisodeId], () => {
    if (episode) {
      api.episodes.historyBy(episode.sonarrEpisodeId);
    }
  });

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
              update={history.refetch}
              promise={(form) =>
                api.episodes.addBlacklist(sonarrSeriesId, sonarrEpisodeId, form)
              }
            ></BlacklistButton>
          );
        },
      },
    ],
    [history.refetch]
  );

  return (
    <BaseModal title={`History - ${episode?.title ?? ""}`} {...props}>
      <QueryOverlay result={history}>
        <PageTable
          emptyText="No History Found"
          columns={columns}
          data={data ?? []}
        ></PageTable>
      </QueryOverlay>
    </BaseModal>
  );
};
