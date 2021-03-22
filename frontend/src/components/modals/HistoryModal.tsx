import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Column } from "react-table";
import { AsyncStateOverlay, HistoryIcon, LanguageText, PageTable } from "..";
import { EpisodesApi, MoviesApi } from "../../apis";
import { BlacklistButton } from "../../generic/blacklist";
import { updateAsyncState } from "../../utilites";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { usePayload } from "./provider";

export const MovieHistoryModal: FunctionComponent<BaseModalProps> = (props) => {
  const { ...modal } = props;

  const movie = usePayload<Item.Movie>(modal.modalKey);

  const [history, setHistory] = useState<AsyncState<History.Movie[]>>({
    updating: false,
    data: [],
  });

  const update = useCallback(() => {
    if (movie) {
      updateAsyncState(MoviesApi.history(movie.radarrId), setHistory, []);
    }
  }, [movie]);

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
            return <LanguageText text={value} long={true}></LanguageText>;
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
      <AsyncStateOverlay state={history}>
        {(data) => (
          <PageTable
            emptyText="No History Found"
            columns={columns}
            data={data}
          ></PageTable>
        )}
      </AsyncStateOverlay>
    </BaseModal>
  );
};

interface EpisodeHistoryProps {}

export const EpisodeHistoryModal: FunctionComponent<
  BaseModalProps & EpisodeHistoryProps
> = (props) => {
  const episode = usePayload<Item.Episode>(props.modalKey);

  const [history, setHistory] = useState<AsyncState<History.Episode[]>>({
    updating: false,
    data: [],
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
            return <LanguageText text={value} long={true}></LanguageText>;
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
      <AsyncStateOverlay state={history}>
        {(data) => (
          <PageTable
            emptyText="No History Found"
            columns={columns}
            data={data}
          ></PageTable>
        )}
      </AsyncStateOverlay>
    </BaseModal>
  );
};
