import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { MoviesApi } from "../../apis";
import { AsyncButton, LanguageText, PageTable } from "../../components";

interface Props {
  blacklist: readonly Blacklist.Movie[];
  update: () => void;
}

const Table: FunctionComponent<Props> = ({ blacklist, update }) => {
  const columns = useMemo<Column<Blacklist.Movie>[]>(
    () => [
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
        Header: "Language",
        accessor: "language",
        Cell: ({ row }) => {
          return (
            <LanguageText
              text={row.original.language!}
              long={true}
            ></LanguageText>
          );
        },
      },
      {
        Header: "Provider",
        accessor: "provider",
      },
      {
        Header: "Date",
        accessor: "timestamp",
      },
      {
        accessor: "subs_id",
        Cell: (row) => {
          const subs_id = row.value;

          return (
            <AsyncButton
              size="sm"
              variant="light"
              promise={() =>
                MoviesApi.deleteBlacklist(false, {
                  provider: row.row.original.provider,
                  subs_id,
                })
              }
              onSuccess={update}
            >
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </AsyncButton>
          );
        },
      },
    ],
    [update]
  );
  return (
    <PageTable
      emptyText="No Blacklisted Movies Subtitles"
      columns={columns}
      data={blacklist}
    ></PageTable>
  );
};

export default Table;
