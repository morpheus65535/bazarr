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
  ActionIcon,
  AsyncStateOverlay,
  SubtitleToolModal,
  EpisodeHistoryModal,
} from "../../Components";

import apis from "../../apis";

import { updateAsyncState } from "../../utilites";

interface Props {
  id: string;
  episodeList: AsyncState<Map<number, Episode[]>>;
}

function mapStateToProps({ series }: StoreState) {
  return {
    episodeList: series.episodeList,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const id = Number.parseInt(props.id);
  const list = props.episodeList;
  const episodes = useMemo(() => list.items.get(id) ?? [], [id, list]);

  const [history, setHistory] = useState<AsyncState<Array<EpisodeHistory>>>({
    updating: true,
    items: [],
  });

  const [modal, setModal] = useState<string>("");
  const [modalItem, setModalItem] = useState<Episode | undefined>(undefined);

  const closeModal = () => {
    setModal("");
  };

  const showModal = (key: string, item: Episode) => {
    setModal(key);
    setModalItem(item);
  };

  const columns: Column<Episode>[] = React.useMemo<Column<Episode>[]>(
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
      },
      {
        Header: "Audio",
        accessor: (d) => d.audio_language.name,
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
        Cell: (row) => {
          return (
            <React.Fragment>
              <ActionIcon icon={faUser}></ActionIcon>
              <ActionIcon
                icon={faHistory}
                onClick={() => {
                  const id = row.value;
                  showModal("history", row.row.original);

                  updateAsyncState(apis.episodes.history(id), setHistory, []);
                }}
              ></ActionIcon>
              <ActionIcon
                icon={faBriefcase}
                onClick={() => {
                  showModal("tools", row.row.original);
                }}
              ></ActionIcon>
            </React.Fragment>
          );
        },
      },
    ],
    []
  );

  const options: TableOptions<Episode> = {
    columns,
    data: episodes,
    initialState: {
      groupBy: ["season"],
      expanded: {
        "season:1": true,
      },
    },
  };

  return (
    <AsyncStateOverlay state={props.episodeList} exist={(item) => item.has(id)}>
      <GroupTable options={options}></GroupTable>
      <SubtitleToolModal
        show={modal === "tools"}
        title={`Tools - ${modalItem?.title}`}
        subtitles={modalItem?.subtitles ?? []}
        onClose={closeModal}
      ></SubtitleToolModal>
      <EpisodeHistoryModal
        show={modal === "history"}
        title={`History - ${modalItem?.title}`}
        history={history}
        onClose={closeModal}
      ></EpisodeHistoryModal>
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(Table);
