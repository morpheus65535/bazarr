import {
  faCheck,
  faExclamationTriangle,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Badge, ProgressBar } from "react-bootstrap";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { seriesUpdateInfoAll } from "../@redux/actions";
import { SeriesApi } from "../apis";
import {
  ActionBadge,
  AsyncStateOverlay,
  BasicTable,
  ItemEditorModal,
  useShowModal,
} from "../components";

interface Props {
  series: AsyncState<Series[]>;
  profiles: LanguagesProfile[];
  update: (id: number) => void;
}

function mapStateToProps({ series, system }: StoreState) {
  const { seriesList } = series;
  return {
    series: seriesList,
    profiles: system.languagesProfiles.items,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const { series, profiles, update } = props;

  const showModal = useShowModal();

  const getProfile = useCallback(
    (id?: number) => {
      if (id) {
        return profiles.find((v) => v.profileId === id);
      }
      return null;
    },
    [profiles]
  );

  const columns: Column<Series>[] = useMemo<Column<Series>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
        className: "text-nowrap",
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
        Header: "Exist",
        accessor: "exist",
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
        Cell: (row) => {
          const profileId = row.value;
          return getProfile(profileId)?.name ?? "";
        },
      },
      {
        Header: "Episodes",
        accessor: "episodeFileCount",
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
        Cell: (row) => (
          <ActionBadge
            icon={faWrench}
            onClick={(e) => {
              showModal("edit", row.row.original);
            }}
          ></ActionBadge>
        ),
      },
    ],
    [getProfile, showModal]
  );

  return (
    <AsyncStateOverlay state={series}>
      {(data) => (
        <React.Fragment>
          <BasicTable
            emptyText="No Series Found"
            columns={columns}
            data={data}
          ></BasicTable>
          <ItemEditorModal
            modalKey="edit"
            submit={(item, form) =>
              SeriesApi.modify({
                seriesid: [(item as Series).sonarrSeriesId],
                profileid: [form.profileid],
              })
            }
            onSuccess={(item) => {
              update((item as Series).sonarrSeriesId);
            }}
          ></ItemEditorModal>
        </React.Fragment>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: seriesUpdateInfoAll })(Table);
