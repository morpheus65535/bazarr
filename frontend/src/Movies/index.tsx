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
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { movieUpdateByRange, movieUpdateInfoAll } from "../@redux/actions";
import { useRawMovies } from "../@redux/hooks";
import { useReduxAction } from "../@redux/hooks/base";
import { MoviesApi } from "../apis";
import { ActionBadge, TextPopover } from "../components";
import BaseItemView from "../generic/BaseItemView";

interface Props {}

const MovieView: FunctionComponent<Props> = () => {
  const [movies] = useRawMovies();
  const load = useReduxAction(movieUpdateByRange);
  const columns: Column<Item.Movie>[] = useMemo<Column<Item.Movie>[]>(
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
        Cell: ({ row, value, isSelecting: select }) => {
          if (select) {
            return value;
          } else {
            const target = `/movies/${row.original.radarrId}`;
            return (
              <TextPopover text={row.original.sceneName} delay={1}>
                <Link to={target}>
                  <span>{value}</span>
                </Link>
              </TextPopover>
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
            const profiles = loose[0] as Profile.Languages[];
            return profiles.find((v) => v.profileId === value)?.name ?? null;
          } else {
            return null;
          }
        },
      },
      {
        Header: "Missing Subtitles",
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
        Cell: ({ row, externalUpdate }) => (
          <ActionBadge
            icon={faWrench}
            onClick={() => externalUpdate && externalUpdate(row, "edit")}
          ></ActionBadge>
        ),
      },
    ],
    []
  );

  return (
    <BaseItemView
      state={movies}
      name="Movies"
      loader={load}
      updateAction={movieUpdateInfoAll}
      columns={columns as Column<Item.Base>[]}
      modify={(form) => MoviesApi.modify(form)}
    ></BaseItemView>
  );
};

export default MovieView;
