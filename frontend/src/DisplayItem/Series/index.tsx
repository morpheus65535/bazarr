import { faWrench } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useMemo } from "react";
import { Badge, ProgressBar } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { QueryKeys } from "src/apis/queries/keys";
import api from "src/apis/raw";
import {
  useLanguageProfiles,
  useSeriesModification,
} from "../../apis/queries/client";
import { ActionBadge } from "../../components";
import { BuildKey } from "../../utilities";
import BaseItemView from "../generic/BaseItemView";

interface Props {}

const SeriesView: FunctionComponent<Props> = () => {
  const { data: profiles } = useLanguageProfiles();
  const { mutateAsync } = useSeriesModification();

  const columns: Column<Item.Series>[] = useMemo<Column<Item.Series>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
        className: "text-nowrap",
        Cell: ({ row, value, isSelecting: select }) => {
          if (select) {
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
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge
              variant="secondary"
              className="mr-2"
              key={BuildKey(v.code2, v.forced, v.hi)}
            >
              {v.name}
            </Badge>
          ));
        },
      },
      {
        Header: "Languages Profile",
        accessor: "profileId",
        Cell: ({ value }) => {
          return profiles?.find((v) => v.profileId === value)?.name ?? null;
        },
      },
      {
        Header: "Episodes",
        accessor: "episodeFileCount",
        selectHide: true,
        Cell: (row) => {
          const { episodeFileCount, episodeMissingCount, profileId } =
            row.row.original;
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

          const color = episodeMissingCount === 0 ? "primary" : "warning";

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
    [profiles]
  );

  return (
    <BaseItemView
      name="Series"
      keys={[QueryKeys.Series]}
      query={(params) => api.series.seriesBy(params)}
      columns={columns}
      modify={mutateAsync}
    ></BaseItemView>
  );
};

export default SeriesView;
