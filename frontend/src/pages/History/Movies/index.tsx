import { useMovieAddBlacklist, useMovieHistoryPagination } from "@/apis/hooks";
import { MutateAction } from "@/components/async";
import { HistoryIcon } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import TextPopover from "@/components/TextPopover";
import HistoryView from "@/pages/views/HistoryView";
import { useTableStyles } from "@/styles";
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

const MoviesHistoryView: FunctionComponent = () => {
  const columns: Column<History.Movie>[] = useMemo<Column<History.Movie>[]>(
    () => [
      {
        accessor: "action",
        Cell: (row) => <HistoryIcon action={row.value}></HistoryIcon>,
      },
      {
        Header: "Name",
        accessor: "title",
        Cell: ({ row, value }) => {
          const { classes } = useTableStyles();
          const target = `/movies/${row.original.radarrId}`;
          return (
            <Anchor className={classes.primary} component={Link} to={target}>
              {value}
            </Anchor>
          );
        },
      },
      {
        Header: "Language",
        accessor: "language",
        Cell: ({ value }) => {
          if (value) {
            return (
              <Badge>
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
        Cell: ({ value }) => {
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
        Cell: ({ row, value }) => {
          const add = useMovieAddBlacklist();
          const { radarrId, provider, subs_id, language, subtitles_path } =
            row.original;

          if (subs_id && provider && language) {
            return (
              <MutateAction
                label="Add to Blacklist"
                disabled={value}
                icon={faFileExcel}
                mutation={add}
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
    []
  );

  const query = useMovieHistoryPagination();

  return (
    <HistoryView name="Movies" query={query} columns={columns}></HistoryView>
  );
};

export default MoviesHistoryView;
