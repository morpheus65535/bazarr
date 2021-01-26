import React, { FunctionComponent, useState, useMemo } from "react";
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
  ContentHeaderButton,
  ContentHeaderGroup,
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

  const [scan, setScan] = useState(false);
  const [search, setSearch] = useState(false);

  const allowEdit = item?.languages instanceof Array ?? false;

  const editButton = useMemo(
    () => (
      <React.Fragment>
        <ContentHeaderButton
          icon={faSearch}
          updating={search}
          onClick={() => {
            setSearch(true);
            if (item) {
              MoviesApi.searchMissing(item.radarrId).finally(() => {
                setSearch(false);
                update(item.radarrId);
              });
            }
          }}
        >
          Search
        </ContentHeaderButton>
        <ContentHeaderButton icon={faUser}>Manual</ContentHeaderButton>
      </React.Fragment>
    ),
    [item, search, update]
  );

  const header = useMemo(
    () => (
      <ContentHeader>
        <ContentHeaderGroup pos="start">
          <ContentHeaderButton
            icon={faSync}
            updating={scan}
            onClick={() => {
              setScan(true);
              if (item) {
                MoviesApi.scanDisk(item.radarrId).finally(() => {
                  setScan(false);
                  update(item.radarrId);
                });
              }
            }}
          >
            Scan Disk
          </ContentHeaderButton>
          {allowEdit && editButton}
          <ContentHeaderButton
            icon={faHistory}
            onClick={() => showModal("history", item)}
          >
            History
          </ContentHeaderButton>
          <ContentHeaderButton
            icon={faToolbox}
            onClick={() => showModal("tools", item)}
          >
            Tools
          </ContentHeaderButton>
        </ContentHeaderGroup>

        <ContentHeaderGroup pos="end">
          <ContentHeaderButton
            disabled={!allowEdit}
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload")}
          >
            Upload
          </ContentHeaderButton>
          <ContentHeaderButton
            icon={faWrench}
            onClick={() => showModal("edit", item)}
          >
            Edit Movie
          </ContentHeaderButton>
        </ContentHeaderGroup>
      </ContentHeader>
    ),
    [allowEdit, editButton, item, scan, update, showModal]
  );

  if (item) {
    return (
      <Container fluid>
        <Helmet>
          <title>{item.title} - Bazarr (Movies)</title>
        </Helmet>
        {header}
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
  } else {
    return <LoadingIndicator></LoadingIndicator>;
  }
};

export default withRouter(
  connect(mapStateToProps, { update: updateMovieInfo })(MovieDetailView)
);
