import React, { FunctionComponent } from "react";
import { Column } from "react-table";

import { connect } from "react-redux";
import { Link } from "react-router-dom";

import {
  ActionIcon,
  BasicTable,
  AsyncStateOverlay,
  HistoryActionIcon,
} from "../../components";

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
        Cell: (row) => (
          <HistoryActionIcon action={row.value}></HistoryActionIcon>
        ),
      },
      {
        Header: "Title",
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
        Header: "Actions",
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
      <BasicTable options={{ columns, data: movieHistory.items }}></BasicTable>
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(Table);
