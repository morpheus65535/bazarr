import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faBriefcase,
  faHistory,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Badge, ButtonGroup } from "react-bootstrap";
import { Column, TableOptions, TableUpdater } from "react-table";
import { useSerieBy } from "../../@redux/hooks";
import { ProvidersApi } from "../../apis";
import {
  ActionButton,
  AsyncStateOverlay,
  EpisodeHistoryModal,
  GroupTable,
  SubtitleToolModal,
  TextPopover,
  useShowModal,
} from "../../components";
import { ManualSearchModal } from "../../components/modals/ManualSearchModal";
import { BuildKey } from "../../utilites";
import { SubtitleAction } from "./components";

interface Props {
  episodes: AsyncState<Item.Episode[]>;
  update: () => void;
}

const download = (item: any, result: SearchResultType) => {
  item = item as Item.Episode;
  const { language, hearing_impaired, forced, provider, subtitle } = result;
  return ProvidersApi.downloadEpisodeSubtitle(
    item.sonarrSeriesId,
    item.sonarrEpisodeId,
    {
      language,
      hi: hearing_impaired,
      forced,
      provider,
      subtitle,
    }
  );
};

const Table: FunctionComponent<Props> = ({ episodes, update }) => {
  const showModal = useShowModal();

  const columns: Column<Item.Episode>[] = useMemo<Column<Item.Episode>[]>(
    () => [
      {
        accessor: "monitored",
        Cell: (row) => {
          return (
            <FontAwesomeIcon
              title={row.value ? "monitored" : "unmonitored"}
              icon={row.value ? faBookmark : farBookmark}
            ></FontAwesomeIcon>
          );
        },
      },
      {
        accessor: "season",
        Cell: (row) => {
          return `Season ${row.value}`;
        },
      },
      {
        Header: "Episode",
        accessor: "episode",
      },
      {
        Header: "Title",
        accessor: "title",
        className: "text-nowrap",
        Cell: ({ value, row }) => (
          <TextPopover text={row.original.sceneName} delay={1}>
            <span>{value}</span>
          </TextPopover>
        ),
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge variant="secondary" key={v.code2}>
              {v.name}
            </Badge>
          ));
        },
      },
      {
        Header: "Subtitles",
        accessor: "missing_subtitles",
        Cell: ({ row }) => {
          const episode = row.original;

          const seriesid = episode.sonarrSeriesId;

          const elements = useMemo(() => {
            const episodeid = episode.sonarrEpisodeId;

            const missing = episode.missing_subtitles.map((val, idx) => (
              <SubtitleAction
                missing
                key={BuildKey(idx, val.code2, "missing")}
                seriesid={seriesid}
                episodeid={episodeid}
                subtitle={val}
              ></SubtitleAction>
            ));

            const subtitles = episode.subtitles.map((val, idx) => (
              <SubtitleAction
                key={BuildKey(idx, val.code2, "valid")}
                seriesid={seriesid}
                episodeid={episodeid}
                subtitle={val}
              ></SubtitleAction>
            ));

            return [...missing, ...subtitles];
          }, [episode, seriesid]);

          return elements;
        },
      },
      {
        Header: "Actions",
        accessor: "sonarrEpisodeId",
        Cell: ({ row, externalUpdate }) => {
          const [serie] = useSerieBy(row.original.sonarrSeriesId);

          return (
            <ButtonGroup>
              <ActionButton
                icon={faUser}
                disabled={serie.data?.profileId === null}
                onClick={() => {
                  externalUpdate && externalUpdate(row, "manual-search");
                }}
              ></ActionButton>
              <ActionButton
                icon={faHistory}
                onClick={() => {
                  externalUpdate && externalUpdate(row, "history");
                }}
              ></ActionButton>
              <ActionButton
                icon={faBriefcase}
                onClick={() => {
                  externalUpdate && externalUpdate(row, "tools");
                }}
              ></ActionButton>
            </ButtonGroup>
          );
        },
      },
    ],
    []
  );

  const updateRow = useCallback<TableUpdater<Item.Episode>>(
    (row, modalKey: string) => {
      if (modalKey === "tools") {
        showModal(modalKey, [row.original]);
      } else {
        showModal(modalKey, row.original);
      }
    },
    [showModal]
  );

  const maxSeason = useMemo(
    () =>
      episodes.data.reduce<number>(
        (prev, curr) => Math.max(prev, curr.season),
        0
      ),
    [episodes]
  );

  const options: TableOptions<Item.Episode> = useMemo(() => {
    return {
      columns,
      data: episodes.data,
      externalUpdate: updateRow,
      initialState: {
        sortBy: [
          { id: "season", desc: true },
          { id: "episode", desc: true },
        ],
        groupBy: ["season"],
        expanded: {
          [`season:${maxSeason}`]: true,
        },
      },
    };
  }, [episodes, columns, maxSeason, updateRow]);

  return (
    <React.Fragment>
      <AsyncStateOverlay state={episodes}>
        {() => (
          <GroupTable
            emptyText="No Episode Found For This Series"
            {...options}
          ></GroupTable>
        )}
      </AsyncStateOverlay>
      <SubtitleToolModal
        modalKey="tools"
        size="lg"
        update={update}
      ></SubtitleToolModal>
      <EpisodeHistoryModal modalKey="history" size="lg"></EpisodeHistoryModal>
      <ManualSearchModal
        modalKey="manual-search"
        onDownload={update}
        onSelect={download}
      ></ManualSearchModal>
    </React.Fragment>
  );
};

export default Table;
