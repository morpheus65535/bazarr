import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { seriesUpdateWantedAll } from "../../@redux/actions";
import { EpisodesApi } from "../../apis";
import { AsyncButton, BaseTable, SubtitleText } from "../../components";

interface Props {
  wanted: WantedEpisode[];
  update: () => void;
}

const Table: FunctionComponent<Props> = ({ wanted, update }) => {
  const columns: Column<WantedEpisode>[] = useMemo<Column<WantedEpisode>[]>(
    () => [
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
        Header: "Missing",
        accessor: "missing_subtitles",
        Cell: (row) => {
          const wanted = row.row.original;
          const hi = wanted.hearing_impaired;
          const seriesid = wanted.sonarrSeriesId;
          const episodeid = wanted.sonarrEpisodeId;

          return row.value.map((item, idx) => (
            <AsyncButton
              as={Badge}
              key={idx}
              className="mx-1 mr-2"
              variant="secondary"
              promise={() =>
                EpisodesApi.downloadSubtitles(seriesid, episodeid, {
                  language: item.code2,
                  hi,
                  forced: false,
                })
              }
              onSuccess={update}
            >
              <SubtitleText className="pr-1" subtitle={item}></SubtitleText>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </AsyncButton>
          ));
        },
      },
    ],
    [update]
  );

  return (
    <BaseTable
      emptyText="No Missing Episodes Subtitles"
      columns={columns}
      data={wanted}
    ></BaseTable>
  );
};

export default connect(undefined, { update: seriesUpdateWantedAll })(Table);
