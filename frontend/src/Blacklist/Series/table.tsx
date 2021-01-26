import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { updateSeriesBlacklist } from "../../@redux/actions";
import { SeriesApi } from "../../apis";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { AsyncButton, AsyncStateOverlay, BasicTable } from "../../components";

interface Props {
  blacklist: AsyncState<SeriesBlacklist[]>;
  update: () => void;
}

function mapStateToProps({ series }: StoreState) {
  return {
    blacklist: series.blacklist,
  };
}

const Table: FunctionComponent<Props> = ({ blacklist, update }) => {
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
          const subs_id = row.value;
          return (
            <AsyncButton
              size="sm"
              variant="light"
              promise={() =>
                SeriesApi.deleteBlacklist(false, {
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
          emptyText="No Blacklisted Series Subtitles"
          columns={columns}
          data={data}
        ></BasicTable>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: updateSeriesBlacklist })(
  Table
);
