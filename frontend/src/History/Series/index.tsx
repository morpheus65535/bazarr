import { faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Badge, OverlayTrigger, Popover } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column, Row } from "react-table";
import { useSeriesHistory } from "../../@redux/hooks";
import { EpisodesApi } from "../../apis";
import { HistoryIcon, LanguageText } from "../../components";
import { BlacklistButton } from "../../generic/blacklist";
import { useAutoUpdate } from "../../utilites/hooks";
import HistoryGenericView from "../generic";

interface Props {}

const SeriesHistoryView: FunctionComponent<Props> = () => {
  const [series, update] = useSeriesHistory();
  useAutoUpdate(update);

  const tableUpdate = useCallback((row: Row<History.Base>) => update(), [
    update,
  ]);

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
              <Badge variant="secondary">
                <LanguageText text={value} long={true}></LanguageText>
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
        className: "text-nowrap",
      },
      {
        accessor: "description",
        Cell: ({ row, value }) => {
          const overlay = (
            <Popover id={`description-${row.id}`}>
              <Popover.Content>{value}</Popover.Content>
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
        accessor: "blacklisted",
        Cell: ({ row, externalUpdate: update }) => {
          const original = row.original;

          const { sonarrEpisodeId, sonarrSeriesId } = original;
          return (
            <BlacklistButton
              history={original}
              update={() => update && update(row)}
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
      columns={columns as Column<History.Base>[]}
      tableUpdater={tableUpdate}
    ></HistoryGenericView>
  );
};

export default SeriesHistoryView;
