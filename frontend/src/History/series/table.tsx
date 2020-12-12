import React, { FunctionComponent } from "react";
import { Column } from "react-table";

import { connect } from "react-redux";
import { Link } from "react-router-dom";

import {
  ActionIcon,
  BasicTable,
  AsyncStateOverlay,
  HistoryIcon,
} from "../../components";

interface Props {
  seriesHistory: AsyncState<SeriesHistory[]>;
}

function mapStateToProps({ series }: StoreState) {
  const { historyList } = series;
  return {
    seriesHistory: historyList,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const { seriesHistory } = props;

  const columns: Column<SeriesHistory>[] = React.useMemo<
    Column<SeriesHistory>[]
  >(
    () => [
      {
        accessor: "action",
        Cell: (row) => <HistoryIcon action={row.value}></HistoryIcon>,
      },
      {
        Header: "Name",
        accessor: "seriesTitle",
        Cell: (row) => {
          const target = `/series/${row.row.original.sonarrSeriesId}`;

          return (
            <Link to={target}>
              <span>{row.value}</span>
            </Link>
          );
        },
      },
      {
        Header: "Episode",
        accessor: "episode_number",
      },
      {
        accessor: "episodeTitle",
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
        accessor: "sonarrEpisodeId",
        Cell: (row) => {
          return null;
        },
      },
    ],
    []
  );

  return (
    <AsyncStateOverlay state={seriesHistory}>
      <BasicTable
        emptyText="Nothing Found in Series History"
        options={{ columns, data: seriesHistory.items }}
      ></BasicTable>
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(Table);
