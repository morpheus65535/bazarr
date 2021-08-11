import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import {
  movieUpdateAll,
  movieUpdateById,
  movieUpdateByRange,
} from "../@redux/actions";
import { useMovieEntities } from "../@redux/hooks";
import { useReduxAction } from "../@redux/hooks/base";
import { MoviesApi } from "../apis";
import { ActionBadge, LanguageText, TextPopover } from "../components";
import BaseItemView from "../generic/BaseItemView";
import { BuildKey } from "../utilites";

interface Props {}

const MovieView: FunctionComponent<Props> = () => {
  const [movies] = useMovieEntities();
  const rangeLoader = useReduxAction(movieUpdateByRange);
  const idLoader = useReduxAction(movieUpdateById);
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
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge
              variant="secondary"
              className="mr-2"
              key={BuildKey(v.code2, v.code2, v.hi)}
            >
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
            const profiles = loose[0] as Language.Profile[];
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
            <Badge
              className="mx-2"
              variant="warning"
              key={BuildKey(v.code2, v.hi, v.forced)}
            >
              <LanguageText text={v}></LanguageText>
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
      rangeLoader={rangeLoader}
      idLoader={idLoader}
      updateAction={movieUpdateAll}
      columns={columns}
      modify={(form) => MoviesApi.modify(form)}
    ></BaseItemView>
  );
};

export default MovieView;
