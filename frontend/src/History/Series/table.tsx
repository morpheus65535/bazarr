import React, { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";

import { connect } from "react-redux";
import { Link } from "react-router-dom";

import {
  BasicTable,
  AsyncStateOverlay,
  HistoryIcon,
  SeriesBlacklistButton,
} from "../../components";
import { updateHistorySeriesList } from "../../@redux/actions";

interface Props {
  seriesHistory: AsyncState<SeriesHistory[]>;
  update: () => void;
}

function mapStateToProps({ series }: StoreState) {
  const { historyList } = series;
  return {
    seriesHistory: historyList,
  };
}

const Table: FunctionComponent<Props> = ({ seriesHistory, update }) => {
  const columns: Column<SeriesHistory>[] = useMemo<Column<SeriesHistory>[]>(
    () => [
      {
        accessor: "action",
        className: "text-center",
        Cell: (row) => <HistoryIcon action={row.value}></HistoryIcon>,
      },
      {
        Header: "Name",
        accessor: "seriesTitle",
        className: "text-nowrap",
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
        className: "text-nowrap",
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
        accessor: "subs_id",
        Cell: (row) => {
          const original = row.row.original;

          return (
            <SeriesBlacklistButton
              seriesid={original.sonarrSeriesId}
              episodeid={original.sonarrEpisodeId}
              update={update}
              {...original}
            ></SeriesBlacklistButton>
          );
        },
      },
    ],
    [update]
  );

  return (
    <AsyncStateOverlay state={seriesHistory}>
      {(data) => (
        <BasicTable
          emptyText="Nothing Found in Series History"
          columns={columns}
          data={data}
        ></BasicTable>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: updateHistorySeriesList })(
  Table
);
