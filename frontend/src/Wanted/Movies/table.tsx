import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { MoviesApi } from "../../apis";
import { AsyncButton, LanguageText, PageTable } from "../../components";

interface Props {
  wanted: readonly Wanted.Movie[];
  update: () => void;
}

const Table: FunctionComponent<Props> = ({ wanted, update }) => {
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
              onSuccess={update}
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
    <PageTable
      emptyText="No Missing Movies Subtitles"
      columns={columns}
      data={wanted}
    ></PageTable>
  );
};

export default Table;
