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
import { connect } from "react-redux";
import { Column, TableOptions, TableUpdater } from "react-table";
import { seriesUpdateInfoAll } from "../../@redux/actions";
import { ProvidersApi } from "../../apis";
import {
  ActionIcon,
  AsyncStateOverlay,
  EpisodeHistoryModal,
  GroupTable,
  SubtitleToolModal,
  useShowModal,
} from "../../components";
import { ManualSearchModal } from "../../components/modals/ManualSearchModal";
import { SubtitleAction } from "./components";

interface Props {
  series: Item.Series;
  episodeList: AsyncState<Map<number, Item.Episode[]>>;
  update: (id: number) => void;
}

function mapStateToProps({ series }: ReduxStore) {
  return {
    episodeList: series.episodeList,
  };
}

const Table: FunctionComponent<Props> = ({ series, episodeList, update }) => {
  const id = series.sonarrSeriesId;
  const list = episodeList;
  const episodes = useMemo(() => list.items.get(id) ?? [], [id, list]);

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
        Cell: (row) => {
          const episode = row.row.original;

          const seriesid = episode.sonarrSeriesId;
          const episodeid = episode.sonarrEpisodeId;

          const elements = useMemo(() => {
            const missing = episode.missing_subtitles.map((val, idx) => (
              <SubtitleAction
                missing
                key={`${idx}-missing`}
                seriesid={seriesid}
                episodeid={episodeid}
                subtitle={val}
              ></SubtitleAction>
            ));

            const existing = episode.subtitles.filter(
              (val) =>
                episode.missing_subtitles.findIndex(
                  (v) => v.code2 === val.code2
                ) === -1
            );

            const subtitles = existing.map((val, idx) => (
              <SubtitleAction
                key={`${idx}-valid`}
                seriesid={seriesid}
                episodeid={episodeid}
                subtitle={val}
              ></SubtitleAction>
            ));

            return [...missing, ...subtitles];
          }, [episode, episodeid, seriesid]);

          return elements;
        },
      },
      {
        Header: "Actions",
        accessor: "sonarrEpisodeId",
        className: "d-flex flex-nowrap",
        Cell: ({ row, update }) => {
          return (
            <ButtonGroup>
              <ActionIcon
                icon={faUser}
                onClick={() => {
                  update && update(row, "manual-search");
                }}
              ></ActionIcon>
              <ActionIcon
                icon={faHistory}
                onClick={() => {
                  update && update(row, "history");
                }}
              ></ActionIcon>
              <ActionIcon
                icon={faBriefcase}
                onClick={() => {
                  update && update(row, "tools");
                }}
              ></ActionIcon>
            </ButtonGroup>
          );
        },
      },
    ],
    []
  );

  const updateRow = useCallback<TableUpdater<Item.Episode>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  const maxSeason = useMemo(
    () =>
      episodes.reduce<number>((prev, curr) => Math.max(prev, curr.season), 0),
    [episodes]
  );

  const options: TableOptions<Item.Episode> = useMemo(() => {
    return {
      columns,
      data: episodes,
      update: updateRow,
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
      <AsyncStateOverlay state={episodeList} exist={(item) => item.has(id)}>
        {() => (
          <GroupTable
            emptyText="No Episode Found For This Series"
            {...options}
          ></GroupTable>
        )}
      </AsyncStateOverlay>
      <SubtitleToolModal modalKey="tools" size="lg"></SubtitleToolModal>
      <EpisodeHistoryModal modalKey="history" size="lg"></EpisodeHistoryModal>
      <ManualSearchModal
        modalKey="manual-search"
        onDownload={() => update(series.sonarrSeriesId)}
        onSelect={(item, result) => {
          item = item as Item.Episode;
          const {
            language,
            hearing_impaired,
            forced,
            provider,
            subtitle,
          } = result;
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
        }}
      ></ManualSearchModal>
    </React.Fragment>
  );
};

export default connect(mapStateToProps, { update: seriesUpdateInfoAll })(Table);
