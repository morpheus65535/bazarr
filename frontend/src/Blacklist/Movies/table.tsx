import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { MoviesApi } from "../../apis";
import {
  AsyncButton,
  LanguageText,
  PageTable,
  TextPopover,
} from "../../components";

interface Props {
  blacklist: readonly Blacklist.Movie[];
}

const Table: FunctionComponent<Props> = ({ blacklist }) => {
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
        Cell: ({ value }) => {
          if (value) {
            return <LanguageText text={value} long></LanguageText>;
          } else {
            return null;
          }
        },
      },
      {
        Header: "Provider",
        accessor: "provider",
      },
      {
        Header: "Date",
        accessor: "timestamp",
        Cell: (row) => {
          if (row.value) {
            return (
              <TextPopover text={row.row.original.parsed_timestamp} delay={1}>
                <span>{row.value}</span>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        accessor: "subs_id",
        Cell: (row) => {
          const subs_id = row.value;

          return (
            <AsyncButton
              size="sm"
              variant="light"
              noReset
              promise={() =>
                MoviesApi.deleteBlacklist(false, {
                  provider: row.row.original.provider,
                  subs_id,
                })
              }
            >
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </AsyncButton>
          );
        },
      },
    ],
    []
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
