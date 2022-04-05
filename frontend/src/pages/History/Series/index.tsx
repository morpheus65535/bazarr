import {
  useEpisodeAddBlacklist,
  useEpisodeHistoryPagination,
} from "@/apis/hooks";
import { HistoryIcon } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import { BlacklistButton } from "@/components/inputs/blacklist";
import TextPopover from "@/components/TextPopover";
import HistoryView from "@/components/views/HistoryView";
import { faInfoCircle, faRecycle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";

const SeriesHistoryView: FunctionComponent = () => {
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
              <Badge color="secondary">
                <Language.Text value={value} long></Language.Text>
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
              <TextPopover text={row.row.original.parsed_timestamp}>
                <Text>{row.value}</Text>
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
          return (
            <TextPopover text={value}>
              <FontAwesomeIcon size="sm" icon={faInfoCircle}></FontAwesomeIcon>
            </TextPopover>
          );
        },
      },
      {
        accessor: "upgradable",
        Cell: (row) => {
          if (row.value) {
            return (
              <TextPopover text="This Subtitles File Is Eligible For An Upgrade.">
                <FontAwesomeIcon size="sm" icon={faRecycle}></FontAwesomeIcon>
              </TextPopover>
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
          const { mutateAsync } = useEpisodeAddBlacklist();
          return (
            <BlacklistButton
              history={original}
              promise={(form) =>
                mutateAsync({
                  seriesId: sonarrSeriesId,
                  episodeId: sonarrEpisodeId,
                  form,
                })
              }
            ></BlacklistButton>
          );
        },
      },
    ],
    []
  );

  const query = useEpisodeHistoryPagination();

  return (
    <HistoryView name="Series" query={query} columns={columns}></HistoryView>
  );
};

export default SeriesHistoryView;
