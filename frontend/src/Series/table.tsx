import React from "react";
import { Column } from "react-table";
import BasicTable from "../components/BasicTable";

import { connect } from "react-redux";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck,
  faExclamationTriangle,
} from "@fortawesome/free-solid-svg-icons";
import { Badge, ProgressBar } from "react-bootstrap";

interface Props {
  series: Array<Series>;
}

function mapStateToProps({ series }: StoreState): Props {
  const { seriesList } = series;
  return {
    series: seriesList.items,
  };
}

function Table(props: Props) {
  const columns: Column<Series>[] = React.useMemo<Column<Series>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
      },
      {
        Header: "Path Exist",
        accessor: "exist",
        Cell: (row) => {
          const exist = row.value;
          return (
            <FontAwesomeIcon
              icon={exist ? faCheck : faExclamationTriangle}
            ></FontAwesomeIcon>
          );
        },
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          const audio_language = row.value;
          return <span>{audio_language.name}</span>;
        },
      },
      {
        Header: "Subtitles Languages",
        accessor: "languages",
        Cell: (row) => {
          const languages = row.value;
          const items = languages.map(
            (val: SeriesLanguage, idx: number): JSX.Element => (
              <Badge className="mx-1" key={idx} variant="secondary">
                {val.code2}
              </Badge>
            )
          );
          return items;
        },
      },
      {
        Header: "Hearing-Impaired",
        accessor: "hearing_impaired",
      },
      {
        Header: "Forced",
        accessor: "forced",
      },
      {
        Header: "Subtitles",
        accessor: "episodeFileCount",
        Cell: (row) => {
          const { episodeFileCount, episodeMissingCount } = row.row.original;
          let progress = 0;
          let label = "";
          if (episodeFileCount === 0) {
            progress = 0.0;
          } else {
            progress = 1.0 - episodeMissingCount / episodeFileCount;
            label = `${
              episodeFileCount - episodeMissingCount
            }/${episodeFileCount}`;
          }

          return (
            <ProgressBar
              min={0}
              max={1}
              now={progress}
              label={label}
            ></ProgressBar>
          );
        },
      },
    ],
    []
  );

  return <BasicTable options={{ columns, data: props.series }}></BasicTable>;
}

export default connect(mapStateToProps)(Table);
