import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { movieUpdateWantedByRange } from "../../@redux/actions";
import { useWantedMovies } from "../../@redux/hooks";
import { useReduxAction } from "../../@redux/hooks/base";
import { MoviesApi } from "../../apis";
import { AsyncButton, LanguageText } from "../../components";
import GenericWantedView from "../generic";

interface Props {}

const WantedMoviesView: FunctionComponent<Props> = () => {
  const [movies, update] = useWantedMovies();

  const loader = useReduxAction(movieUpdateWantedByRange);

  const searchAll = useCallback(
    () => MoviesApi.action({ action: "search-wanted" }),
    []
  );

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
        Cell: (row) => {
          const wanted = row.row.original;
          const hi = wanted.hearing_impaired;
          const movieid = wanted.radarrId;

          return row.value.map((item, idx) => (
            <AsyncButton
              as={Badge}
              key={idx}
              className="mx-1 mr-2"
              variant="secondary"
              promise={() =>
                MoviesApi.downloadSubtitles(movieid, {
                  language: item.code2,
                  hi,
                  forced: false,
                })
              }
              onSuccess={() => update(movieid)}
            >
              <LanguageText className="pr-1" text={item}></LanguageText>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </AsyncButton>
          ));
        },
      },
    ],
    [update]
  );

  return (
    <GenericWantedView
      type="movies"
      columns={columns as Column<Wanted.Base>[]}
      state={movies}
      update={update}
      loader={loader}
      searchAll={searchAll}
    ></GenericWantedView>
  );
};

export default WantedMoviesView;
