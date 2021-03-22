import { faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Badge, OverlayTrigger, Popover } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column, Row } from "react-table";
import { useMoviesHistory } from "../../@redux/hooks";
import { MoviesApi } from "../../apis";
import { HistoryIcon, LanguageText } from "../../components";
import { BlacklistButton } from "../../generic/blacklist";
import { useAutoUpdate } from "../../utilites/hooks";
import HistoryGenericView from "../generic";

interface Props {}

const MoviesHistoryView: FunctionComponent<Props> = () => {
  const [movies, update] = useMoviesHistory();
  useAutoUpdate(update);

  const tableUpdate = useCallback((row: Row<History.Base>) => update(), [
    update,
  ]);

  const columns: Column<History.Movie>[] = useMemo<Column<History.Movie>[]>(
    () => [
      {
        accessor: "action",
        className: "text-center",
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
              <Badge variant="secondary">
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
        Cell: ({ row, externalUpdate }) => {
          const original = row.original;
          return (
            <BlacklistButton
              history={original}
              update={() => externalUpdate && externalUpdate(row)}
              promise={(form) =>
                MoviesApi.addBlacklist(original.radarrId, form)
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
      type="movies"
      state={movies}
      columns={columns as Column<History.Base>[]}
      tableUpdater={tableUpdate}
    ></HistoryGenericView>
  );
};

export default MoviesHistoryView;
