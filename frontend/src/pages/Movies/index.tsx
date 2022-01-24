import { useMovieModification, useMoviesPagination } from "@/apis/hooks";
import { ActionBadge, TextPopover } from "@/components";
import Language from "@/components/bazarr/Language";
import LanguageProfile from "@/components/bazarr/LanguageProfile";
import ItemView from "@/components/views/ItemView";
import { BuildKey } from "@/utilities";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge, Container } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Link } from "react-router-dom";
import { Column } from "react-table";

const MovieView: FunctionComponent = () => {
  const mutation = useMovieModification();

  const query = useMoviesPagination();

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
        Cell: ({ value }) => {
          return <LanguageProfile index={value}></LanguageProfile>;
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
              <Language value={v}></Language>
            </Badge>
          ));
        },
      },
      {
        accessor: "radarrId",
        selectHide: true,
        Cell: ({ row, update }) => {
          return (
            <ActionBadge
              icon={faWrench}
              onClick={() => update && update(row, "edit")}
            ></ActionBadge>
          );
        },
      },
    ],
    []
  );

  return (
    <Container fluid>
      <Helmet>
        <title>Movies - Bazarr</title>
      </Helmet>
      <ItemView query={query} columns={columns} mutation={mutation}></ItemView>
    </Container>
  );
};

export default MovieView;
