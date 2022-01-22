import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import {
  useMovieAction,
  useMovieSubtitleModification,
  useMovieWantedPagination,
} from "src/apis/hooks";
import { AsyncButton, LanguageText } from "../../components";
import WantedView from "../../components/views/WantedView";
import { BuildKey } from "../../utilities";

interface Props {}

const WantedMoviesView: FunctionComponent<Props> = () => {
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
        Cell: ({ row, value }) => {
          const wanted = row.original;
          const { hearing_impaired: hi, radarrId } = wanted;

          const { download } = useMovieSubtitleModification();

          return value.map((item, idx) => (
            <AsyncButton
              as={Badge}
              key={BuildKey(idx, item.code2)}
              className="mx-1 mr-2"
              variant="secondary"
              promise={() =>
                download.mutateAsync({
                  radarrId,
                  form: {
                    language: item.code2,
                    hi,
                    forced: false,
                  },
                })
              }
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

  const { mutateAsync } = useMovieAction();
  const query = useMovieWantedPagination();

  return (
    <WantedView
      name="Movies"
      columns={columns}
      query={query}
      searchAll={() => mutateAsync({ action: "search-wanted" })}
    ></WantedView>
  );
};

export default WantedMoviesView;
