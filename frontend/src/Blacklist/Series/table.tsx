import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { seriesUpdateBlacklist } from "../../@redux/actions";
import { EpisodesApi } from "../../apis";
import { AsyncButton, PageTable } from "../../components";

interface Props {
  blacklist: Blacklist.Episode[];
  update: () => void;
}

const Table: FunctionComponent<Props> = ({ blacklist, update }) => {
  const columns = useMemo<Column<Blacklist.Episode>[]>(
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
                EpisodesApi.deleteBlacklist(false, {
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
      emptyText="No Blacklisted Series Subtitles"
      columns={columns}
      data={blacklist}
    ></PageTable>
  );
};

export default connect(undefined, { update: seriesUpdateBlacklist })(Table);
