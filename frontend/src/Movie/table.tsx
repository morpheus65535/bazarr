import React, { FunctionComponent, MouseEvent } from "react";
import { Column } from "react-table";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Badge } from "react-bootstrap";

import BasicTable from "../components/tables/BasicTable";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faWrench,
  faCheck,
  faBookmark,
  faExclamationTriangle,
} from "@fortawesome/free-solid-svg-icons";

interface Props {
  movies: Movie[];
  openMovieEditor?: (movie: Movie) => void;
}

function mapStateToProps({ movie }: StoreState) {
  const { movieList } = movie;
  return {
    movies: movieList.items,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const { movies, openMovieEditor: onOpenMovieEditor } = props;

  const columns: Column<Movie>[] = React.useMemo<Column<Movie>[]>(
    () => [
      {
        accessor: "monitored",
        Cell: (row) => {
          const monitored = row.value === "True";

          if (monitored) {
            return <FontAwesomeIcon icon={faBookmark}></FontAwesomeIcon>;
          } else {
            return <span></span>;
          }
        },
      },
      {
        Header: "Name",
        accessor: "title",
        Cell: (row) => {
          const target = `/movies/${row.row.original.radarrId}`;
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
              (val: Language): JSX.Element => (
                <Badge className="mx-1" key={val.name} variant="secondary">
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
        Header: "Missing Subtitles",
        accessor: "missing_subtitles",
        Cell: (row) => {
          const subtitles = row.value;
          return subtitles.map((val) => (
            <Badge className="mx-1" key={val.name} variant="secondary">
              {val.code2}
            </Badge>
          ));
        },
      },
      {
        accessor: "radarrId",
        Cell: (row) => {
          return (
            <Badge
              as="a"
              href=""
              className="mx-1"
              variant="secondary"
              onClick={(e: MouseEvent) => {
                e.preventDefault();
                onOpenMovieEditor && onOpenMovieEditor(row.row.original);
              }}
            >
              <FontAwesomeIcon icon={faWrench}></FontAwesomeIcon>
            </Badge>
          );
        },
      },
    ],
    [onOpenMovieEditor]
  );

  return <BasicTable options={{ columns, data: movies }}></BasicTable>;
};

export default connect(mapStateToProps)(Table);
