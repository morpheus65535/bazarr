import React, { FunctionComponent } from "react";
import { Column } from "react-table";

import { connect } from "react-redux";
import { Link } from "react-router-dom";

import {
  BasicTable,
  AsyncStateOverlay,
  HistoryIcon,
} from "../../Components";

interface Props {
  movieHistory: AsyncState<MovieHistory[]>;
}

function mapStateToProps({ movie }: StoreState) {
  const { historyList } = movie;
  return {
    movieHistory: historyList,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const { movieHistory } = props;

  const columns: Column<MovieHistory>[] = React.useMemo<Column<MovieHistory>[]>(
    () => [
      {
        accessor: "action",
        Cell: (row) => <HistoryIcon action={row.value}></HistoryIcon>,
      },
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
        Header: "Date",
        accessor: "timestamp",
      },
      {
        Header: "Description",
        accessor: "description",
      },
      {
        accessor: "radarrId",
        Cell: (row) => {
          return null;
        },
      },
    ],
    []
  );

  return (
    <AsyncStateOverlay state={movieHistory}>
      {(data) => (
        <BasicTable
          emptyText="Nothing Found in Movies History"
          options={{ columns, data }}
        ></BasicTable>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(Table);
