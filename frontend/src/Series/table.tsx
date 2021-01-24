import React, {
  FunctionComponent,
  useState,
  useCallback,
  useMemo,
} from "react";
import { Column } from "react-table";
import {
  BasicTable,
  ActionIconBadge,
  AsyncStateOverlay,
  ItemEditorModal,
} from "../components";

import { connect } from "react-redux";
import { Link } from "react-router-dom";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck,
  faExclamationTriangle,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { ProgressBar, Badge } from "react-bootstrap";

import { updateSeriesInfo } from "../@redux/actions";
import { SeriesApi } from "../apis";

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

  const [modal, setModal] = useState<string>("");
  const [item, setItem] = useState<Series | undefined>(undefined);

  const getProfile = useCallback(
    (id?: number) => {
      if (id) {
        return profiles.find((v) => v.profileId === id);
      }
      return null;
    },
    [profiles]
  );

  const showModal = useCallback((key: string, item: Series) => {
    setItem(item);
    setModal(key);
  }, []);

  const hideModal = useCallback(() => {
    setModal("");
  }, []);

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
          return (
            <FontAwesomeIcon
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
          const { episodeFileCount, episodeMissingCount } = row.row.original;
          let progress = 0;
          let label = "";
          if (episodeFileCount === 0) {
            progress = 0.0;
          } else {
            progress = 1.0 - episodeMissingCount / episodeFileCount;
            label = `${
              episodeFileCount - episodeMissingCount
            }/${episodeFileCount}`;
          }

          const color = progress === 1.0 ? "info" : "warning";

          return (
            <ProgressBar
              className="my-a"
              variant={color}
              min={0}
              max={1}
              now={progress}
              label={label}
            ></ProgressBar>
          );
        },
      },
      {
        accessor: "sonarrSeriesId",
        Cell: (row) => (
          <ActionIconBadge
            icon={faWrench}
            onClick={(e) => {
              showModal("edit", row.row.original);
            }}
          ></ActionIconBadge>
        ),
      },
    ],
    [getProfile, showModal]
  );

  return (
    <React.Fragment>
      <AsyncStateOverlay state={series}>
        {(data) => (
          <BasicTable
            emptyText="No Series Found"
            columns={columns}
            data={data}
          ></BasicTable>
        )}
      </AsyncStateOverlay>
      <ItemEditorModal
        show={modal === "edit"}
        onClose={hideModal}
        key={item?.title}
        item={item}
        submit={(form) => SeriesApi.modify(item!.sonarrSeriesId, form)}
        onSuccess={() => {
          hideModal();
          update(item!.sonarrSeriesId);
        }}
      ></ItemEditorModal>
    </React.Fragment>
  );
};

export default connect(mapStateToProps, { update: updateSeriesInfo })(Table);
