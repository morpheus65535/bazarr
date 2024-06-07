/* eslint-disable camelcase */
import {
  useEpisodeAddBlacklist,
  useEpisodeHistoryPagination,
} from "@/apis/hooks";
import { MutateAction } from "@/components/async";
import { HistoryIcon } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import StateIcon from "@/components/StateIcon";
import TextPopover from "@/components/TextPopover";
import HistoryView from "@/pages/views/HistoryView";
import {
  faFileExcel,
  faInfoCircle,
  faRecycle,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Anchor, Badge, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";

const SeriesHistoryView: FunctionComponent = () => {
  const columns: Column<History.Episode>[] = useMemo<Column<History.Episode>[]>(
    () => [
      {
        accessor: "action",
        Cell: ({ value }) => <HistoryIcon action={value}></HistoryIcon>,
      },
      {
        Header: "Series",
        accessor: "seriesTitle",
        Cell: (row) => {
          const target = `/series/${row.row.original.sonarrSeriesId}`;

          return (
            <Anchor className="table-primary" component={Link} to={target}>
              {row.value}
            </Anchor>
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
        Cell: ({ value }) => {
          return <Text className="table-no-wrap">{value}</Text>;
        },
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
        Header: "Match",
        accessor: "matches",
        Cell: (row) => {
          const { matches, dont_matches: dont } = row.row.original;
          if (matches.length || dont.length) {
            return (
              <StateIcon
                matches={matches}
                dont={dont}
                isHistory={true}
              ></StateIcon>
            );
          } else {
            return null;
          }
        },
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
        Header: "Info",
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
        Header: "Upgrade",
        accessor: "upgradable",
        Cell: (row) => {
          if (row.value) {
            return (
              <TextPopover text="This Subtitle File Is Eligible For An Upgrade.">
                <FontAwesomeIcon size="sm" icon={faRecycle}></FontAwesomeIcon>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        Header: "Blacklist",
        accessor: "blacklisted",
        Cell: ({ row, value }) => {
          const {
            sonarrEpisodeId,
            sonarrSeriesId,
            provider,
            subs_id,
            language,
            subtitles_path,
          } = row.original;
          const add = useEpisodeAddBlacklist();

          if (subs_id && provider && language) {
            return (
              <MutateAction
                label="Add to Blacklist"
                disabled={value}
                icon={faFileExcel}
                mutation={add}
                args={() => ({
                  seriesId: sonarrSeriesId,
                  episodeId: sonarrEpisodeId,
                  form: {
                    provider,
                    subs_id,
                    subtitles_path,
                    language: language.code2,
                  },
                })}
              ></MutateAction>
            );
          } else {
            return null;
          }
        },
      },
    ],
    [],
  );

  const query = useEpisodeHistoryPagination();

  return (
    <HistoryView name="Series" query={query} columns={columns}></HistoryView>
  );
};

export default SeriesHistoryView;
