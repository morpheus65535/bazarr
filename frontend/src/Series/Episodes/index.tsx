import React, { FunctionComponent, useEffect, useMemo, useState } from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { Container, Row } from "react-bootstrap";

import { faHdd, faAdjust } from "@fortawesome/free-solid-svg-icons";

import {
  faSync,
  faSearch,
  faCloudUploadAlt,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { updateSeriesInfo } from "../../@redux/actions";

import {
  ContentHeader,
  ItemOverview,
  ItemEditorModal,
  SeriesUploadModal,
  LoadingIndicator,
  useShowModal,
} from "../../components";

import { SeriesApi } from "../../apis";

import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Series[]>;
  update: (id: number) => void;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesList } = series;
  return {
    seriesList,
  };
}

const SeriesEpisodesView: FunctionComponent<Props> = (props) => {
  const { update, match, seriesList } = props;
  const id = Number.parseInt(match.params.id);
  const list = seriesList.items;

  const item = useMemo(() => list.find((val) => val.sonarrSeriesId === id), [
    list,
    id,
  ]);

  const details = useMemo(
    () => [
      {
        icon: faHdd,
        text: `${item?.episodeFileCount} files`,
      },
      {
        icon: faAdjust,
        text: item?.seriesType ?? "",
      },
    ],
    [item]
  );

  const showModal = useShowModal();

  const [scan, setScan] = useState(false);
  const [search, setSearch] = useState(false);

  useEffect(() => {
    update(id);
  }, [update, id]);

  if (!item) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <Container fluid>
      <Helmet>
        <title>{item.title} - Bazarr (Series)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.Button
            icon={faSync}
            updating={scan}
            onClick={() => {
              setScan(true);
              SeriesApi.scanDisk(id).finally(() => {
                setScan(false);
                update(id);
              });
            }}
          >
            Scan Disk
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faSearch}
            updating={search}
            disabled={item.episodeFileCount === 0 ?? false}
            onClick={() => {
              setSearch(true);
              SeriesApi.searchMissing(id).finally(() => {
                setSearch(false);
                update(id);
              });
            }}
          >
            Search
          </ContentHeader.Button>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={item.episodeFileCount === 0 ?? false}
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload")}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            onClick={() => showModal("edit", item)}
          >
            Edit Series
          </ContentHeader.Button>
        </ContentHeader.Group>
      </ContentHeader>
      <Row>
        <ItemOverview item={item} details={details}></ItemOverview>
      </Row>
      <Row>
        <Table id={id}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(item, form) =>
          SeriesApi.modify((item as Series).sonarrSeriesId, form)
        }
        onSuccess={(item) => update((item as Series).sonarrSeriesId)}
      ></ItemEditorModal>
      <SeriesUploadModal series={item} modalKey="upload"></SeriesUploadModal>
    </Container>
  );
};

export default withRouter(
  connect(mapStateToProps, { update: updateSeriesInfo })(SeriesEpisodesView)
);
