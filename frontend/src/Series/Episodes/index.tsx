import React, { FunctionComponent, useEffect, useMemo, useState } from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { Container, Row } from "react-bootstrap";

import {
  faSync,
  faSearch,
  faCloudUploadAlt,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { updateEpisodeList } from "../../@redux/actions";

import {
  ContentHeader,
  ContentHeaderButton,
  ContentHeaderGroup,
  ItemOverview,
  ItemEditorModal,
  LoadingOverlay,
} from "../../Components";

import { SeriesApi } from "../../apis";

import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Series[]>;
  updateEpisodeList: (id: number) => void;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesList } = series;
  return {
    seriesList,
  };
}

const SeriesEpisodesView: FunctionComponent<Props> = (props) => {
  const { updateEpisodeList, match, seriesList } = props;
  const id = Number.parseInt(match.params.id);
  const list = seriesList.items;

  const item = useMemo(() => list.find((val) => val.sonarrSeriesId === id), [
    list,
    id,
  ]);

  const [modal, setModal] = useState("");
  const [scan, setScan] = useState(false);
  const [search, setSearch] = useState(false);

  useEffect(() => {
    updateEpisodeList(id);
  }, [updateEpisodeList, id]);

  const header = (
    <ContentHeader>
      <ContentHeaderGroup pos="start">
        <ContentHeaderButton
          icon={faSync}
          updating={scan}
          onClick={() => {
            setScan(true);
            SeriesApi.scanDisk(id).finally(() => {
              setScan(false);
              updateEpisodeList(id);
            });
          }}
        >
          Scan Disk
        </ContentHeaderButton>
        <ContentHeaderButton
          icon={faSearch}
          updating={search}
          onClick={() => {
            setSearch(true);
            SeriesApi.searchMissing(id).finally(() => {
              setSearch(false);
              updateEpisodeList(id);
            });
          }}
        >
          Search
        </ContentHeaderButton>
      </ContentHeaderGroup>
      <ContentHeaderGroup pos="end">
        <ContentHeaderButton icon={faCloudUploadAlt}>
          Upload
        </ContentHeaderButton>
        <ContentHeaderButton icon={faWrench} onClick={() => setModal("edit")}>
          Edit Series
        </ContentHeaderButton>
      </ContentHeaderGroup>
    </ContentHeader>
  );

  if (item) {
    const details = [
      item.audio_language.name,
      item.mapped_path,
      `${item.episodeFileCount} files`,
      item.seriesType,
      item.tags,
    ];

    return (
      <Container fluid>
        <Helmet>
          <title>{item.title} - Bazarr (Series)</title>
        </Helmet>
        {header}
        <Row>
          <ItemOverview item={item} details={details}></ItemOverview>
        </Row>
        <Row>
          <Table id={id}></Table>
        </Row>
        <ItemEditorModal
          show={modal === "edit"}
          title={item.title}
          item={item}
          onClose={() => setModal("")}
          submit={(form) => SeriesApi.modify(item.sonarrSeriesId, form)}
          onSuccess={() => {
            setModal("");
            // TODO: Websocket
            updateEpisodeList(item.sonarrSeriesId);
          }}
        ></ItemEditorModal>
      </Container>
    );
  } else {
    return <LoadingOverlay></LoadingOverlay>;
  }
};

export default withRouter(
  connect(mapStateToProps, { updateEpisodeList })(SeriesEpisodesView)
);
