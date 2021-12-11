import { faInfoCircle, faRecycle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge, OverlayTrigger, Popover } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { episodesUpdateHistoryByRange } from "../../@redux/actions";
import { useSeriesHistory } from "../../@redux/hooks";
import { useReduxAction } from "../../@redux/hooks/base";
import { EpisodesApi } from "../../apis";
import { HistoryIcon, LanguageText, TextPopover } from "../../components";
import { BlacklistButton } from "../../DisplayItem/generic/blacklist";
import HistoryGenericView from "../generic";

interface Props {}

const SeriesHistoryView: FunctionComponent<Props> = () => {
  const series = useSeriesHistory();
  const loader = useReduxAction(episodesUpdateHistoryByRange);

  const columns: Column<History.Episode>[] = useMemo<Column<History.Episode>[]>(
    () => [
      {
        accessor: "action",
        className: "text-center",
        Cell: ({ value }) => <HistoryIcon action={value}></HistoryIcon>,
      },
      {
        Header: "Series",
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
        Header: "Title",
        accessor: "episodeTitle",
      },
      {
        Header: "Language",
        accessor: "language",
        Cell: ({ value }) => {
          if (value) {
            return (
              <Badge bg="secondary">
                <LanguageText text={value} long></LanguageText>
              </Badge>
            );
          } else {
            return null;
          }
        },
      },
      {
        Header: "Score",
        accessor: "score",
      },
      {
        Header: "Date",
        accessor: "timestamp",
        Cell: (row) => {
          if (row.value) {
            return (
              <TextPopover text={row.row.original.parsed_timestamp} delay={1}>
                <span>{row.value}</span>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        accessor: "description",
        Cell: ({ row, value }) => {
          const overlay = (
            <Popover id={`description-${row.id}`}>
              <Popover.Body>{value}</Popover.Body>
            </Popover>
          );
          return (
            <OverlayTrigger overlay={overlay}>
              <FontAwesomeIcon size="sm" icon={faInfoCircle}></FontAwesomeIcon>
            </OverlayTrigger>
          );
        },
      },
      {
        accessor: "upgradable",
        Cell: (row) => {
          const overlay = (
            <Popover id={`description-${row.row.id}`}>
              <Popover.Body>
                This Subtitles File Is Eligible For An Upgrade.
              </Popover.Body>
            </Popover>
          );
          if (row.value) {
            return (
              <OverlayTrigger overlay={overlay}>
                <FontAwesomeIcon size="sm" icon={faRecycle}></FontAwesomeIcon>
              </OverlayTrigger>
            );
          } else {
            return null;
          }
        },
      },
      {
        accessor: "blacklisted",
        Cell: ({ row }) => {
          const original = row.original;

          const { sonarrEpisodeId, sonarrSeriesId } = original;
          return (
            <BlacklistButton
              history={original}
              promise={(form) =>
                EpisodesApi.addBlacklist(sonarrSeriesId, sonarrEpisodeId, form)
              }
            ></BlacklistButton>
          );
        },
      },
    ],
    []
  );

  return (
    <HistoryGenericView
      type="series"
      state={series}
      loader={loader}
      columns={columns}
    ></HistoryGenericView>
  );
};

export default SeriesHistoryView;
