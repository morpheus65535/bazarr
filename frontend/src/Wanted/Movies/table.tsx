import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { MoviesApi } from "../../apis";
import { AsyncButton, LanguageText, PageTable } from "../../components";

interface Props {
  wanted: readonly Item.Movie[];
  update: () => void;
}

const Table: FunctionComponent<Props> = ({ wanted, update }) => {
  const columns: Column<Item.Movie>[] = useMemo<Column<Item.Movie>[]>(
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
          const hi = wanted.hearing_impaired;
          const movieid = wanted.radarrId;

          return value.map((item, idx) => (
            <AsyncButton
              as={Badge}
              key={idx}
              className="px-1 mr-2"
              variant="secondary"
              promise={() =>
                MoviesApi.downloadSubtitles(movieid, {
                  hi,
                  language: item.code2,
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
