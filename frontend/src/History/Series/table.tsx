import { faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge, OverlayTrigger, Popover } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { useSeriesHistory } from "../../@redux/hooks";
import {
  AsyncStateOverlay,
  HistoryIcon,
  LanguageText,
  PageTable,
} from "../../components";
import { SeriesBlacklistButton } from "../../generic/blacklist";

interface Props {}

const Table: FunctionComponent<Props> = () => {
  const [seriesHistory, update] = useSeriesHistory();

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
                <LanguageText text={value}></LanguageText>
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
        accessor: "exist",
        Cell: ({ row }) => {
          const original = row.original;

          const { sonarrEpisodeId, sonarrSeriesId } = original;
          return (
            <SeriesBlacklistButton
              seriesid={sonarrSeriesId}
              episodeid={sonarrEpisodeId}
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
        <PageTable
          emptyText="Nothing Found in Series History"
          columns={columns}
          data={data}
        ></PageTable>
      )}
    </AsyncStateOverlay>
  );
};

export default Table;
