import { useMovieAddBlacklist, useMovieHistoryPagination } from "@/apis/hooks";
import { HistoryIcon } from "@/components/bazarr/HistoryIcon";
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
        className: "text-nowrap",
        Cell: (row) => {
          const target = `/movies/${row.row.original.radarrId}`;

          return (
            <Link to={target}>
              <span>{row.value}</span>
            </Link>
          );
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
        Cell: ({ row }) => {
          const { radarrId } = row.original;
          const { mutateAsync } = useMovieAddBlacklist();
          return (
            <BlacklistButton
              history={row.original}
              promise={(form) => mutateAsync({ id: radarrId, form })}
            ></BlacklistButton>
          );
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
