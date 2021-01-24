import React, { FunctionComponent, useState, useMemo } from "react";
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
  ActionIconBadge,
  AsyncStateOverlay,
  SubtitleToolModal,
  EpisodeHistoryModal,
} from "../../components";

interface Props {
  id: number;
  episodeList: AsyncState<Map<number, Episode[]>>;
}

function mapStateToProps({ series }: StoreState) {
  return {
    episodeList: series.episodeList,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const id = props.id;
  const list = props.episodeList;
  const episodes = useMemo(() => list.items.get(id) ?? [], [id, list]);

  const [modal, setModal] = useState<string>("");
  const [modalItem, setModalItem] = useState<Episode | undefined>(undefined);

  const closeModal = () => {
    setModal("");
  };

  const showModal = (key: string, item: Episode) => {
    setModalItem(item);
    setModal(key);
  };

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
          const missing = row.value.map(
            (val: Subtitle, idx: number): JSX.Element => (
              <Badge className="mx-1" key={`${idx}-missing`} variant="warning">
                {val.code2}
              </Badge>
            )
          );

          // Subtitles
          const subtitles = row.row.original.subtitles
            // TODO: Performance
            .filter(
              (val) =>
                row.value.findIndex((item) => item.code2 === val.code2) === -1
            )
            .map(
              (val: Subtitle, idx: number): JSX.Element => (
                <Badge className="mx-1" key={`${idx}-sub`} variant="secondary">
                  {val.code2}
                </Badge>
              )
            );

          return [...missing, ...subtitles];
        },
      },
      {
        Header: "Actions",
        accessor: "sonarrEpisodeId",
        className: "d-flex flex-nowrap",
        Cell: (row) => {
          return (
            <React.Fragment>
              <ActionIconBadge icon={faUser}></ActionIconBadge>
              <ActionIconBadge
                icon={faHistory}
                onClick={() => {
                  showModal("history", row.row.original);
                }}
              ></ActionIconBadge>
              <ActionIconBadge
                icon={faBriefcase}
                onClick={() => {
                  showModal("tools", row.row.original);
                }}
              ></ActionIconBadge>
            </React.Fragment>
          );
        },
      },
    ],
    []
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
      <AsyncStateOverlay
        state={props.episodeList}
        exist={(item) => item.has(id)}
      >
        {(data) => (
          <GroupTable
            emptyText="No Episode Found For This Series"
            {...options}
          ></GroupTable>
        )}
      </AsyncStateOverlay>
      <SubtitleToolModal
        size="lg"
        show={modal === "tools"}
        title={`Tools - ${modalItem?.title}`}
        subtitles={modalItem?.subtitles ?? []}
        onClose={closeModal}
      ></SubtitleToolModal>
      <EpisodeHistoryModal
        size="lg"
        show={modal === "history"}
        episode={modalItem}
        onClose={closeModal}
      ></EpisodeHistoryModal>
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(Table);
