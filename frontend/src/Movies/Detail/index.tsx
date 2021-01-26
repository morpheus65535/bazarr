import React, { FunctionComponent, useState } from "react";
import { connect } from "react-redux";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { Helmet } from "react-helmet";

import {
  faSync,
  faHistory,
  faToolbox,
  faWrench,
  faUser,
  faSearch,
  faCloudUploadAlt,
} from "@fortawesome/free-solid-svg-icons";

import { Container, Row } from "react-bootstrap";

import {
  ContentHeader,
  ItemEditorModal,
  ItemOverview,
  LoadingIndicator,
  SubtitleToolModal,
  MovieHistoryModal,
  MovieUploadModal,
  useShowModal,
} from "../../components";

import Table from "./table";
import { MoviesApi } from "../../apis";
import { updateMovieInfo } from "../../@redux/actions";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  movieList: AsyncState<Movie[]>;
  update: (id: number) => void;
}

function mapStateToProps({ movie }: StoreState) {
  const { movieList } = movie;
  return {
    movieList,
  };
}

const MovieDetailView: FunctionComponent<Props> = ({
  movieList,
  match,
  update,
}) => {
  const list = movieList.items;
  const id = Number.parseInt(match.params.id);
  const item = list.find((val) => val.radarrId === id);

  const showModal = useShowModal();

  if (!item) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  const allowEdit = item?.languages instanceof Array ?? false;

  return (
    <Container fluid>
      <Helmet>
        <title>{item.title} - Bazarr (Movies)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.AsyncButton
            icon={faSync}
            promise={() => MoviesApi.scanDisk(item.radarrId)}
            onSuccess={() => update(item.radarrId)}
          >
            Scan Disk
          </ContentHeader.AsyncButton>
          <ContentHeader.AsyncButton
            icon={faSearch}
            promise={() => MoviesApi.searchMissing(item.radarrId)}
            onSuccess={() => update(item.radarrId)}
          >
            Search
          </ContentHeader.AsyncButton>
          <ContentHeader.Button icon={faUser}>Manual</ContentHeader.Button>
          <ContentHeader.Button
            icon={faHistory}
            onClick={() => showModal("history", item)}
          >
            History
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faToolbox}
            onClick={() => showModal("tools", item)}
          >
            Tools
          </ContentHeader.Button>
        </ContentHeader.Group>

        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={!allowEdit}
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload")}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            onClick={() => showModal("edit", item)}
          >
            Edit Movie
          </ContentHeader.Button>
        </ContentHeader.Group>
      </ContentHeader>
      <Row>
        <ItemOverview item={item} details={[]}></ItemOverview>
      </Row>
      <Row>
        <Table movie={item}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(item, form) =>
          MoviesApi.modify((item as Movie).radarrId, form)
        }
        onSuccess={() => update(id)}
      ></ItemEditorModal>
      <SubtitleToolModal size="lg" modalKey="tools"></SubtitleToolModal>
      <MovieHistoryModal size="lg" modalKey="history"></MovieHistoryModal>
      <MovieUploadModal modalKey="upload" movie={item}></MovieUploadModal>
    </Container>
  );
};

export default withRouter(
  connect(mapStateToProps, { update: updateMovieInfo })(MovieDetailView)
);
