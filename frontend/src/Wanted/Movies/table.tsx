import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Column } from "react-table";
import { connect } from "react-redux";
import { Link } from "react-router-dom";

import { BasicTable, AsyncStateOverlay, AsyncButton } from "../../components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSearch } from "@fortawesome/free-solid-svg-icons";

import { updateWantedMovies } from "../../@redux/actions";

import { MoviesApi } from "../../apis";

interface Props {
  wanted: AsyncState<WantedMovie[]>;
  update: () => void;
}

function mapStateToProps({ movie }: StoreState) {
  const { wantedMovieList } = movie;
  return {
    wanted: wantedMovieList,
  };
}

const Table: FunctionComponent<Props> = ({ wanted, update }) => {
  const columns: Column<WantedMovie>[] = useMemo<Column<WantedMovie>[]>(
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
          const wanted = row.row.original;
          const hi = wanted.hearing_impaired;
          const movieid = wanted.radarrId;

          return row.value.map((item, idx) => (
            <AsyncButton
              as={Badge}
              key={idx}
              className="px-1"
              variant="secondary"
              promise={() =>
                MoviesApi.downloadSubtitles(movieid, {
                  hi,
                  language: item.code2,
                  forced: false,
                })
              }
              onSuccess={update}
            >
              <span className="mr-1">{item.code2}</span>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </AsyncButton>
          ));
        },
      },
    ],
    [update]
  );

  return (
    <AsyncStateOverlay state={wanted}>
      {(data) => (
        <BasicTable
          emptyText="No Missing Movies Subtitles"
          columns={columns}
          data={data}
        ></BasicTable>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: updateWantedMovies })(Table);
