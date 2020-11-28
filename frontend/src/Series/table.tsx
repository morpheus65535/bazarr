import React, { FunctionComponent, MouseEvent } from "react";
import { Column } from "react-table";
import BasicTable from "../components/BasicTable";

import { connect } from "react-redux";
import { Link } from "react-router-dom";

import { openSeriesEditModal } from "../redux/actions/series";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck,
  faExclamationTriangle,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { Badge, ProgressBar } from "react-bootstrap";

interface Props {
  series: Array<Series>;
  openSeriesEditModal: (series: Series) => void;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesList } = series;
  return {
    series: seriesList.items,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const { series, openSeriesEditModal } = props;

  const columns: Column<Series>[] = React.useMemo<Column<Series>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
        Cell: (row) => {
          const target = `/series/${row.row.original.sonarrSeriesId}`;
          return (
            <Link to={target}>
              <span>{row.value}</span>
            </Link>
          );
        },
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
          if (languages instanceof Array) {
            const items = languages.map(
              (val: SeriesLanguage, idx: number): JSX.Element => (
                <Badge className="mx-1" key={idx} variant="secondary">
                  {val.code2}
                </Badge>
              )
            );
            return items;
          } else {
            return <span />;
          }
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
              className="my-a"
              min={0}
              max={1}
              now={progress}
              label={label}
            ></ProgressBar>
          );
        },
      },
      {
        Header: "",
        accessor: "overview",
        Cell: (row) => {
          return (
            <Badge
              as="a"
              href=""
              className="mx-1"
              variant="secondary"
              onClick={(e: MouseEvent) => {
                e.preventDefault();
                openSeriesEditModal(row.row.original);
              }}
            >
              <FontAwesomeIcon icon={faWrench}></FontAwesomeIcon>
            </Badge>
          );
        },
      },
    ],
    []
  );

  return <BasicTable options={{ columns, data: series }}></BasicTable>;
};

export default connect(mapStateToProps, {
  openSeriesEditModal,
})(Table);
