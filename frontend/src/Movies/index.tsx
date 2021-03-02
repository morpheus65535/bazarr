import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faCheck,
  faExclamationTriangle,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { movieUpdateInfoAll } from "../@redux/actions";
import { MoviesApi } from "../apis";
import { ActionBadge } from "../components";
import BaseItemView from "../generic/BaseItemView";

interface Props {
  movies: AsyncState<Movie[]>;
  update: (id?: number) => void;
}

function mapStateToProps({ movie }: StoreState) {
  const { movieList } = movie;
  return {
    movies: movieList,
  };
}

const MovieView: FunctionComponent<Props> = ({ movies, update }) => {
  const columns: Column<Movie>[] = useMemo<Column<Movie>[]>(
    () => [
      {
        accessor: "monitored",
        selectHide: true,
        Cell: ({ value }) => (
          <FontAwesomeIcon
            title={value ? "monitored" : "unmonitored"}
            icon={value ? faBookmark : farBookmark}
          ></FontAwesomeIcon>
        ),
      },
      {
        Header: "Name",
        accessor: "title",
        className: "text-nowrap",
        Cell: ({ row, value, isSelecting }) => {
          if (isSelecting) {
            return value;
          } else {
            const target = `/movies/${row.original.radarrId}`;
            return (
              <Link to={target} title={row.original.sceneName ?? value}>
                <span>{value}</span>
              </Link>
            );
          }
        },
      },
      {
        Header: "Exist",
        accessor: "exist",
        selectHide: true,
        Cell: ({ row, value }) => {
          const exist = value;
          const { path } = row.original;
          return (
            <FontAwesomeIcon
              title={path}
              icon={exist ? faCheck : faExclamationTriangle}
            ></FontAwesomeIcon>
          );
        },
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge variant="secondary" className="mr-2" key={v.code2}>
              {v.name}
            </Badge>
          ));
        },
      },
      {
        Header: "Languages Profile",
        accessor: "profileId",
        Cell: ({ value, loose }) => {
          if (loose) {
            // Define in generic/BaseItemView/table.tsx
            const profiles = loose[0] as LanguagesProfile[];
            return profiles.find((v) => v.profileId === value)?.name ?? null;
          } else {
            return null;
          }
        },
      },
      {
        accessor: "missing_subtitles",
        selectHide: true,
        Cell: (row) => {
          const missing = row.value;
          return missing.map((v) => (
            <Badge className="mx-2" variant="warning" key={v.code2}>
              {v.code2}
            </Badge>
          ));
        },
      },
      {
        accessor: "radarrId",
        selectHide: true,
        Cell: ({ row, update }) => (
          <ActionBadge
            icon={faWrench}
            onClick={() => update && update(row, "edit")}
          ></ActionBadge>
        ),
      },
    ],
    []
  );

  return (
    <BaseItemView
      items={movies}
      name="Movies"
      update={update}
      columns={columns as Column<BaseItem>[]}
      modify={(form) => MoviesApi.modify(form)}
    ></BaseItemView>
  );
};

export default connect(mapStateToProps, { update: movieUpdateInfoAll })(
  MovieView
);
