import React, { FunctionComponent } from "react";
import { Column } from "react-table";
import BasicTable from "../../components/tables/BasicTable";

import { connect } from "react-redux";
import { Link } from "react-router-dom";

import { ActionIcon } from "../../components";

interface Props {
  seriesHistory: SeriesHistory[];
}

function mapStateToProps({ series }: StoreState) {
  const { historyList } = series;
  return {
    seriesHistory: historyList.items,
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

  return <BasicTable options={{ columns, data: seriesHistory }}></BasicTable>;
};

export default connect(mapStateToProps)(Table);
