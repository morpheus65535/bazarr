import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { movieUpdateBlacklist } from "../../@redux/actions";
import { MoviesApi } from "../../apis";
import { AsyncButton, PageTable } from "../../components";

interface Props {
  blacklist: Blacklist.Movie[];
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
        accessor: (d) => d.language.name,
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

export default connect(undefined, { update: movieUpdateBlacklist })(Table);
