import React from "react";
import { Column } from "react-table";
import { connect } from "react-redux";
import { Link } from "react-router-dom";

import BasicTable from "../../components/tables/BasicTable";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { Badge, Button } from "react-bootstrap";

interface Props {
  wanted: Array<WantedEpisode>;
  //   search: (id: string) => void;
}

function mapStateToProps({ series }: StoreState): Props {
  const { wantedSeriesList } = series;
  return {
    wanted: wantedSeriesList.items,
  };
}

function Table(props: Props): JSX.Element {
  const columns: Column<WantedEpisode>[] = React.useMemo<
    Column<WantedEpisode>[]
  >(
    () => [
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
        Header: "Episode Title",
        accessor: "episodeTitle",
      },
      {
        Header: "Missing Subtitle(s)",
        accessor: "missing_subtitles",
        Cell: (row) => {
          return row.value.map((item, idx) => (
            <Button
              as={Badge}
              className="mx-1 p-1"
              key={idx}
              variant="secondary"
              onClick={(event) => {
                event.preventDefault();
              }}
            >
              <span className="mr-1">{item.code2}</span>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </Button>
          ));
        },
      },
    ],
    []
  );

  return <BasicTable options={{ columns, data: props.wanted }}></BasicTable>;
}

export default connect(mapStateToProps, {})(Table);
