import React, { FunctionComponent, useState } from "react";
import { Column } from "react-table";
import {
  BasicTable,
  ActionIcon,
  AsyncStateOverlay,
  BooleanIndicator,
  ItemEditorModal,
} from "../Components";

import { connect } from "react-redux";
import { Link } from "react-router-dom";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck,
  faExclamationTriangle,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { Badge, ProgressBar } from "react-bootstrap";

import { updateSeriesInfo } from "../@redux/actions";
import { SeriesApi } from "../apis";

interface Props {
  series: AsyncState<Series[]>;
  update: (id: number) => void;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesList } = series;
  return {
    series: seriesList,
  };
}

const Table: FunctionComponent<Props> = (props) => {
  const { series, update } = props;

  const [modal, setModal] = useState<string>("");
  const [item, setItem] = useState<Series | undefined>(undefined);

  const showModal = (key: string, item: Series) => {
    setItem(item);
    setModal(key);
  };

  const hideModal = () => {
    setModal("");
  };

  const columns: Column<Series>[] = React.useMemo<Column<Series>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
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
          const audio_language = row.value;
          return <span>{audio_language.name}</span>;
        },
      },
      {
        Header: "Languages",
        accessor: "languages",
        Cell: (row) => {
          const languages = row.value;
          if (languages instanceof Array) {
            const items = languages.map(
              (val: Language, idx: number): JSX.Element => (
                <Badge className="mx-1" key={idx} variant="secondary">
                  {val.code2}
                </Badge>
              )
            );
            return items;
          } else {
            return <span />;
          }
        },
      },
      {
        Header: "HI",
        accessor: "hearing_impaired",
        Cell: (row) => {
          return <BooleanIndicator value={row.value}></BooleanIndicator>;
        },
      },
      {
        Header: "Forced",
        accessor: "forced",
        Cell: (row) => {
          return <BooleanIndicator value={row.value}></BooleanIndicator>;
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
          <ActionIcon
            icon={faWrench}
            onClick={(e) => {
              showModal("edit", row.row.original);
            }}
          ></ActionIcon>
        ),
      },
    ],
    []
  );

  return (
    <AsyncStateOverlay state={series}>
      <BasicTable
        emptyText="No Series Found"
        options={{ columns, data: series.items }}
      ></BasicTable>
      <ItemEditorModal
        show={modal === "edit"}
        title={item?.title}
        onClose={hideModal}
        key={item?.title}
        item={item}
        submit={(form) => SeriesApi.modify(item!.sonarrSeriesId, form)}
        onSuccess={() => {
          hideModal();
          // TODO: Websocket
          update(item!.sonarrSeriesId);
        }}
      ></ItemEditorModal>
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: updateSeriesInfo })(Table);
