import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { useMovieAction } from "src/apis/hooks";
import api from "src/apis/raw";
import { AsyncButton, LanguageText } from "../../components";
import { BuildKey } from "../../utilities";
import GenericWantedView from "../generic";

interface Props {}

const WantedMoviesView: FunctionComponent<Props> = () => {
  const { mutateAsync } = useMovieAction();

  const columns: Column<Wanted.Movie>[] = useMemo<Column<Wanted.Movie>[]>(
    () => [
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
        Header: "Missing",
        accessor: "missing_subtitles",
        Cell: ({ row, value, update }) => {
          const wanted = row.original;
          const hi = wanted.hearing_impaired;
          const movieid = wanted.radarrId;

          return value.map((item, idx) => (
            <AsyncButton
              as={Badge}
              key={BuildKey(idx, item.code2)}
              className="mx-1 mr-2"
              variant="secondary"
              promise={() =>
                api.movies.downloadSubtitles(movieid, {
                  language: item.code2,
                  hi,
                  forced: false,
                })
              }
              onSuccess={() => update && update(row, movieid)}
            >
              <LanguageText className="pr-1" text={item}></LanguageText>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </AsyncButton>
          ));
        },
      },
    ],
    []
  );

  return (
    <GenericWantedView
      type="movies"
      columns={columns}
      query={(param) => api.movies.wanted(param)}
      searchAll={() => mutateAsync({ action: "search-wanted" })}
    ></GenericWantedView>
  );
};

export default WantedMoviesView;
