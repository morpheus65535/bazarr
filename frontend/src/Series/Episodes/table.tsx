import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Column, TableOptions } from "react-table";

import { connect } from "react-redux";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBookmark,
  faUser,
  faCloudUploadAlt,
  faBriefcase,
} from "@fortawesome/free-solid-svg-icons";

import { GroupTable, ActionIcon, AsyncStateOverlay } from "../../components";

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
  const { items, updating } = props.episodeList;
  const episodes = useMemo(() => items.get(id) ?? [], [id, items, updating]);

  const columns: Column<Episode>[] = React.useMemo<Column<Episode>[]>(
    () => [
      {
        accessor: "monitored",
        Cell: (row) => {
          return <FontAwesomeIcon icon={faBookmark}></FontAwesomeIcon>;
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
        Header: "Audio Language",
        accessor: (d) => d.audio_language.name,
      },
      {
        Header: "Subtitles",
        accessor: "subtitles",
        Cell: (row) => {
          const items = row.value.map(
            (val: Subtitle, idx: number): JSX.Element => (
              <Badge className="mx-1" key={idx} variant="success">
                {val.code2}
              </Badge>
            )
          );
          return items;
        },
      },
      {
        Header: "Missing",
        accessor: "missing_subtitles",
        Cell: (row) => {
          const items = row.value.map(
            (val: Subtitle, idx: number): JSX.Element => (
              <Badge className="mx-1" key={idx} variant="secondary">
                {val.code2}
              </Badge>
            )
          );
          return items;
        },
      },
      {
        Header: "Actions",
        accessor: "sonarrEpisodeId",
        Cell: (row) => {
          return (
            <React.Fragment>
              <ActionIcon icon={faUser}></ActionIcon>
              <ActionIcon icon={faCloudUploadAlt}></ActionIcon>
              <ActionIcon icon={faBriefcase}></ActionIcon>
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
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(Table);
