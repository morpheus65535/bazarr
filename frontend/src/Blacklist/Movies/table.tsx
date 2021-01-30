import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { AsyncButton, AsyncStateOverlay, BasicTable } from "../../components";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { MoviesApi } from "../../apis";
import { movieUpdateBlacklist } from "../../@redux/actions";

interface Props {
  blacklist: AsyncState<MovieBlacklist[]>;
  update: () => void;
}

function mapStateToProps({ movie }: StoreState) {
  return {
    blacklist: movie.blacklist,
  };
}

const Table: FunctionComponent<Props> = ({ blacklist, update }) => {
  const columns = useMemo<Column<MovieBlacklist>[]>(
    () => [
      {
        Header: "Series",
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
    <AsyncStateOverlay state={blacklist}>
      {(data) => (
        <BasicTable
          emptyText="No Blacklisted Movies Subtitles"
          columns={columns}
          data={data}
        ></BasicTable>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: movieUpdateBlacklist })(
  Table
);
