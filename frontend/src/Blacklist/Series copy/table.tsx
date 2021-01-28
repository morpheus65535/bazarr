import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { ActionIcon, AsyncStateOverlay, BasicTable } from "../../components";

interface Props {
  blacklist: AsyncState<SeriesBlacklist[]>;
}

function mapStateToProps({ series }: StoreState) {
  return {
    blacklist: series.blacklist,
  };
}

const Table: FunctionComponent<Props> = ({ blacklist }) => {
  const columns = useMemo<Column<SeriesBlacklist>[]>(
    () => [
      {
        Header: "Series",
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
          const id = row.value;
          return <ActionIcon icon={faTrash}></ActionIcon>;
        },
      },
    ],
    []
  );
  return (
    <AsyncStateOverlay state={blacklist}>
      {(data) => (
        <BasicTable
          emptyText="No Blacklisted Series Subtitles"
          columns={columns}
          data={data}
        ></BasicTable>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(Table);
