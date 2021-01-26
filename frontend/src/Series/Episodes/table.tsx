import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Column, TableOptions } from "react-table";

import { connect } from "react-redux";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBookmark,
  faUser,
  faBriefcase,
  faHistory,
} from "@fortawesome/free-solid-svg-icons";

import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";

import {
  GroupTable,
  ActionBadge,
  AsyncStateOverlay,
  SubtitleToolModal,
  EpisodeHistoryModal,
  useShowModal,
} from "../../components";

import { SubtitleAction } from "./components";

interface Props {
  series: Series;
  episodeList: AsyncState<Map<number, Episode[]>>;
  profileList: LanguagesProfile[];
}

function mapStateToProps({ series, system }: StoreState) {
  return {
    episodeList: series.episodeList,
    profileList: system.languagesProfiles.items,
  };
}

const Table: FunctionComponent<Props> = ({
  series,
  episodeList,
  profileList,
}) => {
  const id = series.sonarrSeriesId;
  const list = episodeList;
  const episodes = useMemo(() => list.items.get(id) ?? [], [id, list]);

  const profile = useMemo(
    () => profileList.find((v) => v.profileId === series.profileId),
    [profileList, series.profileId]
  );

  const showModal = useShowModal();

  const columns: Column<Episode>[] = useMemo<Column<Episode>[]>(
    () => [
      {
        accessor: "monitored",
        Cell: (row) => {
          return (
            <FontAwesomeIcon
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
                profile={profile}
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
                profile={profile}
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
        Cell: (row) => {
          const episode = row.row.original;
          return (
            <React.Fragment>
              <ActionBadge icon={faUser}></ActionBadge>
              <ActionBadge
                icon={faHistory}
                onClick={() => {
                  showModal("history", episode);
                }}
              ></ActionBadge>
              <ActionBadge
                icon={faBriefcase}
                onClick={() => {
                  showModal("tools", episode);
                }}
              ></ActionBadge>
            </React.Fragment>
          );
        },
      },
    ],
    [showModal, profile]
  );

  const maxSeason = useMemo(
    () =>
      episodes.reduce<number>((prev, curr) => Math.max(prev, curr.season), 0),
    [episodes]
  );

  const options: TableOptions<Episode> = useMemo(() => {
    return {
      columns,
      data: episodes,
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
  }, [episodes, columns, maxSeason]);

  return (
    <React.Fragment>
      <AsyncStateOverlay state={episodeList} exist={(item) => item.has(id)}>
        {(data) => (
          <GroupTable
            emptyText="No Episode Found For This Series"
            {...options}
          ></GroupTable>
        )}
      </AsyncStateOverlay>
      <SubtitleToolModal size="lg" modalKey="tools"></SubtitleToolModal>
      <EpisodeHistoryModal size="lg" modalKey="history"></EpisodeHistoryModal>
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(Table);
