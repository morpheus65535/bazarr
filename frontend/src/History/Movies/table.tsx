import { faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge, OverlayTrigger, Popover } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { useMoviesHistory } from "../../@redux/hooks";
import {
  AsyncStateOverlay,
  HistoryIcon,
  LanguageText,
  PageTable,
} from "../../components";
import { MoviesBlacklistButton } from "../../generic/blacklist";
import { useAutoUpdate } from "../../utilites/hooks";

interface Props {}

const Table: FunctionComponent<Props> = () => {
  const [history, update] = useMoviesHistory();
  useAutoUpdate(update);

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
        accessor: "exist",
        Cell: ({ row }) => {
          const original = row.original;
          return (
            <MoviesBlacklistButton
              update={update}
              {...original}
            ></MoviesBlacklistButton>
          );
        },
      },
    ],
    [update]
  );

  return (
    <AsyncStateOverlay state={history}>
      {(data) => (
        <PageTable
          emptyText="Nothing Found in Movies History"
          columns={columns}
          data={data}
        ></PageTable>
      )}
    </AsyncStateOverlay>
  );
};

export default Table;
