import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Badge } from "react-bootstrap";

import {
  BasicTable,
  ActionBadge,
  AsyncStateOverlay,
  ItemEditorModal,
  useShowModal,
} from "../components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faWrench,
  faCheck,
  faBookmark,
  faExclamationTriangle,
} from "@fortawesome/free-solid-svg-icons";

import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";

import { MoviesApi } from "../apis";
import { updateMovieInfo } from "../@redux/actions";

interface Props {
  movies: AsyncState<Movie[]>;
  update: (id: number) => void;
  profiles: LanguagesProfile[];
}

function mapStateToProps({ movie, system }: StoreState) {
  const { movieList } = movie;
  return {
    movies: movieList,
    profiles: system.languagesProfiles.items,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const { movies, profiles, update } = props;

  const showModal = useShowModal();

  const getProfile = useCallback(
    (id?: number) => {
      if (id) {
        return profiles.find((v) => v.profileId === id);
      }
      return undefined;
    },
    [profiles]
  );

  const columns: Column<Movie>[] = useMemo<Column<Movie>[]>(
    () => [
      {
        accessor: "monitored",
        Cell: (row) => {
          const monitored = row.value;

          return (
            <FontAwesomeIcon
              icon={monitored ? faBookmark : farBookmark}
            ></FontAwesomeIcon>
          );
        },
      },
      {
        Header: "Name",
        accessor: "title",
        className: "text-nowrap",
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
        Header: "Exist",
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
        Cell: (row) => {
          const profileId = row.value;
          return getProfile(profileId)?.name ?? "";
        },
      },
      {
        accessor: "radarrId",
        Cell: (row) => (
          <ActionBadge
            icon={faWrench}
            onClick={(e) => showModal("edit", row.row.original)}
          ></ActionBadge>
        ),
      },
    ],
    [getProfile, showModal]
  );

  return (
    <React.Fragment>
      <AsyncStateOverlay state={movies}>
        {(data) => (
          <BasicTable
            emptyText="No Movies Found"
            columns={columns}
            data={data}
          ></BasicTable>
        )}
      </AsyncStateOverlay>
      <ItemEditorModal
        modalKey="edit"
        submit={(item, form) =>
          MoviesApi.modify((item as Movie).radarrId, form)
        }
        onSuccess={(item) => update((item as Movie).radarrId)}
      ></ItemEditorModal>
    </React.Fragment>
  );
};

export default connect(mapStateToProps, { update: updateMovieInfo })(Table);
