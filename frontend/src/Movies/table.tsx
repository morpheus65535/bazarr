import React, { FunctionComponent, useState, useCallback } from "react";
import { Column } from "react-table";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Badge } from "react-bootstrap";

import {
  BasicTable,
  ActionIconBadge,
  AsyncStateOverlay,
  ItemEditorModal,
} from "../Components";

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

  const [modal, setModal] = useState<string>("");
  const [item, setItem] = useState<Movie | undefined>(undefined);

  const getProfile = useCallback(
    (id: number) => {
      return profiles.find((v) => v.profileId === id);
    },
    [profiles]
  );

  const showModal = useCallback((key: string, item: Movie) => {
    setItem(item);
    setModal(key);
  }, []);

  const hideModal = useCallback(() => {
    setModal("");
  }, []);

  const columns: Column<Movie>[] = React.useMemo<Column<Movie>[]>(
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
            <Badge variant="secondary" key={v.code2}>
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
          <ActionIconBadge
            icon={faWrench}
            onClick={(e) => showModal("edit", row.row.original)}
          ></ActionIconBadge>
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
            options={{ columns, data }}
          ></BasicTable>
        )}
      </AsyncStateOverlay>
      <ItemEditorModal
        show={modal === "edit"}
        title={item?.title}
        key={item?.title}
        item={item}
        onClose={hideModal}
        submit={(form) => MoviesApi.modify(item!.radarrId, form)}
        onSuccess={() => {
          hideModal();
          update(item!.radarrId);
        }}
      ></ItemEditorModal>
    </React.Fragment>
  );
};

export default connect(mapStateToProps, { update: updateMovieInfo })(Table);
