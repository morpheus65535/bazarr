import React from "react";
import { Column } from "react-table";
import { connect } from "react-redux";
import { Link } from "react-router-dom";

import { BasicTable, AsyncStateOverlay, ActionBadge } from "../../components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSearch } from "@fortawesome/free-solid-svg-icons";

interface Props {
  wanted: AsyncState<WantedMovie[]>;
  //   search: (id: string) => void;
}

function mapStateToProps({ movie }: StoreState): Props {
  const { wantedMovieList } = movie;
  return {
    wanted: wantedMovieList,
  };
}

function Table(props: Props): JSX.Element {
  const columns: Column<WantedMovie>[] = React.useMemo<Column<WantedMovie>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
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
        Header: "Missing",
        accessor: "missing_subtitles",
        Cell: (row) => {
          return row.value.map((item, idx) => (
            <ActionBadge key={idx} onClick={() => {}}>
              <span className="mr-1">{item.code2}</span>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </ActionBadge>
          ));
        },
      },
    ],
    []
  );

  return (
    <AsyncStateOverlay state={props.wanted}>
      {(data) => (
        <BasicTable
          emptyText="No Missing Movies Subtitles"
          options={{ columns, data }}
        ></BasicTable>
      )}
    </AsyncStateOverlay>
  );
}

export default connect(mapStateToProps, {})(Table);
