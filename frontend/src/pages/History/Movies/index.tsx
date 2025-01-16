/* eslint-disable camelcase */
import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router";
import { Anchor, Badge, Text } from "@mantine/core";
import {
  faFileExcel,
  faInfoCircle,
  faRecycle,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ColumnDef } from "@tanstack/react-table";
import { useMovieAddBlacklist, useMovieHistoryPagination } from "@/apis/hooks";
import { MutateAction } from "@/components/async";
import { HistoryIcon } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import StateIcon from "@/components/StateIcon";
import TextPopover from "@/components/TextPopover";
import HistoryView from "@/pages/views/HistoryView";

const MoviesHistoryView: FunctionComponent = () => {
  const addToBlacklist = useMovieAddBlacklist();

  const columns = useMemo<ColumnDef<History.Movie>[]>(
    () => [
      {
        id: "action",
        cell: ({ row }) => (
          <HistoryIcon action={row.original.action}></HistoryIcon>
        ),
      },
      {
        header: "Name",
        accessorKey: "title",
        cell: ({ row }) => {
          const target = `/movies/${row.original.radarrId}`;
          return (
            <Anchor className="table-primary" component={Link} to={target}>
              {row.original.title}
            </Anchor>
          );
        },
      },
      {
        header: "Language",
        accessorKey: "language",
        cell: ({
          row: {
            original: { language },
          },
        }) => {
          if (language) {
            return (
              <Badge>
                <Language.Text value={language} long></Language.Text>
              </Badge>
            );
          } else {
            return null;
          }
        },
      },
      {
        header: "Score",
        accessorKey: "score",
      },
      {
        header: "Match",
        accessorKey: "matches",
        cell: (row) => {
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
        header: "Date",
        accessorKey: "timestamp",
        cell: ({
          row: {
            original: { timestamp, parsed_timestamp },
          },
        }) => {
          if (timestamp) {
            return (
              <TextPopover text={parsed_timestamp}>
                <Text>{timestamp}</Text>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        header: "Info",
        accessorKey: "description",
        cell: ({
          row: {
            original: { description },
          },
        }) => {
          return (
            <TextPopover text={description}>
              <FontAwesomeIcon size="sm" icon={faInfoCircle}></FontAwesomeIcon>
            </TextPopover>
          );
        },
      },
      {
        header: "Upgradable",
        accessorKey: "upgradable",
        cell: ({
          row: {
            original: { upgradable },
          },
        }) => {
          if (upgradable) {
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
        header: "Blacklist",
        accessorKey: "blacklisted",
        cell: ({ row }) => {
          const {
            blacklisted,
            radarrId,
            provider,
            subs_id,
            language,
            subtitles_path,
          } = row.original;

          if (subs_id && provider && language) {
            return (
              <MutateAction
                label="Add to Blacklist"
                disabled={blacklisted}
                icon={faFileExcel}
                mutation={addToBlacklist}
                args={() => ({
                  id: radarrId,
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
    [addToBlacklist],
  );

  const query = useMovieHistoryPagination();

  return (
    <HistoryView name="Movies" query={query} columns={columns}></HistoryView>
  );
};

export default MoviesHistoryView;
