import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { seriesUpdateWantedByRange } from "../../@redux/actions";
import { useWantedSeries } from "../../@redux/hooks";
import { useReduxAction } from "../../@redux/hooks/base";
import { EpisodesApi, SeriesApi } from "../../apis";
import { AsyncButton, LanguageText } from "../../components";
import GenericWantedView from "../generic";

interface Props {}

const WantedSeriesView: FunctionComponent<Props> = () => {
  const [series, update] = useWantedSeries();

  const loader = useReduxAction(seriesUpdateWantedByRange);

  const searchAll = useCallback(
    () => SeriesApi.action({ action: "search-wanted" }),
    []
  );

  const columns: Column<Wanted.Episode>[] = useMemo<Column<Wanted.Episode>[]>(
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
        Cell: ({ row, externalUpdate: update, value }) => {
          const wanted = row.original;
          const hi = wanted.hearing_impaired;
          const seriesid = wanted.sonarrSeriesId;
          const episodeid = wanted.sonarrEpisodeId;

          return value.map((item, idx) => (
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
              onSuccess={() => update && update(row, episodeid)}
            >
              <LanguageText className="pr-1" text={item}></LanguageText>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </AsyncButton>
          ));
        },
      },
    ],
    []
  );

  return (
    <GenericWantedView
      type="series"
      columns={columns as Column<Wanted.Base>[]}
      state={series}
      update={update}
      loader={loader}
      searchAll={searchAll}
    ></GenericWantedView>
  );
};

export default WantedSeriesView;
