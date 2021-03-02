import {
  faCheck,
  faExclamationTriangle,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge, ProgressBar } from "react-bootstrap";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { seriesUpdateInfoAll } from "../@redux/actions";
import { SeriesApi } from "../apis";
import { ActionBadge } from "../components";
import BaseItemView from "../generic/BaseItemView";

interface Props {
  series: AsyncState<Item.Series[]>;
  update: (id?: number) => void;
}

function mapStateToProps({ series }: ReduxStore) {
  const { seriesList } = series;
  return {
    series: seriesList,
  };
}

const SeriesView: FunctionComponent<Props> = ({ series, update }) => {
  const columns: Column<Item.Series>[] = useMemo<Column<Item.Series>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
        className: "text-nowrap",
        Cell: ({ row, value, isSelecting }) => {
          if (isSelecting) {
            return value;
          } else {
            const target = `/series/${row.original.sonarrSeriesId}`;
            return (
              <Link to={target}>
                <span>{value}</span>
              </Link>
            );
          }
        },
      },
      {
        Header: "Exist",
        accessor: "exist",
        selectHide: true,
        Cell: (row) => {
          const exist = row.value;
          const { path } = row.row.original;
          return (
            <FontAwesomeIcon
              title={path}
              icon={exist ? faCheck : faExclamationTriangle}
            ></FontAwesomeIcon>
          );
        },
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge variant="secondary" className="mr-2" key={v.code2}>
              {v.name}
            </Badge>
          ));
        },
      },
      {
        Header: "Languages Profile",
        accessor: "profileId",
        Cell: ({ value, loose }) => {
          if (loose) {
            // Define in generic/BaseItemView/table.tsx
            const profiles = loose[0] as Profile.Languages[];
            return profiles.find((v) => v.profileId === value)?.name ?? null;
          } else {
            return null;
          }
        },
      },
      {
        Header: "Episodes",
        accessor: "episodeFileCount",
        selectHide: true,
        Cell: (row) => {
          const {
            episodeFileCount,
            episodeMissingCount,
            profileId,
          } = row.row.original;
          let progress = 0;
          let label = "";
          if (episodeFileCount === 0 || !profileId) {
            progress = 0.0;
          } else {
            progress = episodeFileCount - episodeMissingCount;
            label = `${
              episodeFileCount - episodeMissingCount
            }/${episodeFileCount}`;
          }

          const color = episodeMissingCount === 0 ? "success" : "warning";

          return (
            <ProgressBar
              className="my-a"
              variant={color}
              min={0}
              max={episodeFileCount}
              now={progress}
              label={label}
            ></ProgressBar>
          );
        },
      },
      {
        accessor: "sonarrSeriesId",
        selectHide: true,
        Cell: ({ row, update }) => (
          <ActionBadge
            icon={faWrench}
            onClick={() => {
              update && update(row, "edit");
            }}
          ></ActionBadge>
        ),
      },
    ],
    []
  );

  return (
    <BaseItemView
      items={series}
      name="Series"
      update={update}
      columns={columns as Column<Item.Base>[]}
      modify={(form) => SeriesApi.modify(form)}
    ></BaseItemView>
  );
};

export default connect(mapStateToProps, { update: seriesUpdateInfoAll })(
  SeriesView
);
