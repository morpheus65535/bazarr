import React, { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { useItemUpdater, useMoviesHistory } from "../../@redux/hooks";
import { AsyncStateOverlay, HistoryIcon, PageTable } from "../../components";
import { MoviesBlacklistButton } from "../../components/speical";

interface Props {}

const Table: FunctionComponent<Props> = () => {
  const [history, update] = useMoviesHistory();
  useItemUpdater(update);

  const columns: Column<History.Movie>[] = useMemo<Column<History.Movie>[]>(
    () => [
      {
        accessor: "action",
        className: "text-center",
        Cell: (row) => <HistoryIcon action={row.value}></HistoryIcon>,
      },
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
        Header: "Date",
        accessor: "timestamp",
        className: "text-nowrap",
      },
      {
        Header: "Description",
        accessor: "description",
      },
      {
        accessor: "exist",
        Cell: ({ row }) => {
          const original = row.original;
          return (
            <MoviesBlacklistButton
              update={update}
              {...original}
            ></MoviesBlacklistButton>
          );
        },
      },
    ],
    [update]
  );

  return (
    <AsyncStateOverlay state={history}>
      {(data) => (
        <PageTable
          emptyText="Nothing Found in Movies History"
          columns={columns}
          data={data}
        ></PageTable>
      )}
    </AsyncStateOverlay>
  );
};

export default Table;
