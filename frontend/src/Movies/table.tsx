import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faCheck,
  faExclamationTriangle,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column, TableUpdater } from "react-table";
import { movieUpdateInfoAll } from "../@redux/actions";
import { MoviesApi } from "../apis";
import {
  ActionBadge,
  BaseTable,
  ItemEditorModal,
  useShowModal,
} from "../components";

interface Props {
  movies: Movie[];
  update: (id: number) => void;
  profiles: LanguagesProfile[];
}

function mapStateToProps({ system }: StoreState) {
  return {
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

  const updateRow = useCallback<TableUpdater<Movie>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  const columns: Column<Movie>[] = useMemo<Column<Movie>[]>(
    () => [
      {
        accessor: "monitored",
        Cell: (row) => {
          const monitored = row.value;

          return (
            <FontAwesomeIcon
              title={monitored ? "monitored" : "unmonitored"}
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
          const { mapped_path } = row.row.original;
          return (
            <FontAwesomeIcon
              title={mapped_path}
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
        accessor: "missing_subtitles",
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
        Cell: ({ row, update }) => (
          <ActionBadge
            icon={faWrench}
            onClick={() => update && update(row, "edit")}
          ></ActionBadge>
        ),
      },
    ],
    [getProfile]
  );

  return (
    <React.Fragment>
      <BaseTable
        emptyText="No Movies Found"
        columns={columns}
        data={movies}
        update={updateRow}
      ></BaseTable>
      <ItemEditorModal
        modalKey="edit"
        submit={(item, form) =>
          MoviesApi.modify({
            radarrid: [(item as Movie).radarrId],
            profileid: [form.profileid],
          })
        }
        onSuccess={(item) => update((item as Movie).radarrId)}
      ></ItemEditorModal>
    </React.Fragment>
  );
};

export default connect(mapStateToProps, { update: movieUpdateInfoAll })(Table);
