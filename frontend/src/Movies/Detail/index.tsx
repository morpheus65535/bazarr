import {
  faCloudUploadAlt,
  faHistory,
  faSearch,
  faSync,
  faToolbox,
  faUser,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useState } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Redirect, RouteComponentProps, withRouter } from "react-router-dom";
import { useMovieBy, useProfileBy } from "../../@redux/hooks";
import { MoviesApi, ProvidersApi } from "../../apis";
import {
  ContentHeader,
  ItemEditorModal,
  LoadingIndicator,
  MovieHistoryModal,
  MovieUploadModal,
  SubtitleToolModal,
  useShowModal,
} from "../../components";
import { ManualSearchModal } from "../../components/modals/ManualSearchModal";
import ItemOverview from "../../generic/ItemOverview";
import { RouterEmptyPath } from "../../special-pages/404";
import { useOnLoadedOnce } from "../../utilites";
import Table from "./table";

const download = (item: any, result: SearchResultType) => {
  item = item as Item.Movie;
  const { language, hearing_impaired, forced, provider, subtitle } = result;
  return ProvidersApi.downloadMovieSubtitle(item.radarrId, {
    language,
    hi: hearing_impaired,
    forced,
    provider,
    subtitle,
  });
};

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {}

const MovieDetailView: FunctionComponent<Props> = ({ match }) => {
  const id = Number.parseInt(match.params.id);
  const [movie] = useMovieBy(id);
  const item = movie.content;

  const profile = useProfileBy(movie.content?.profileId);

  const showModal = useShowModal();

  const [valid, setValid] = useState(true);

  useOnLoadedOnce(() => {
    if (movie.content === null) {
      setValid(false);
    }
  }, movie);

  if (isNaN(id) || !valid) {
    return <Redirect to={RouterEmptyPath}></Redirect>;
  }

  if (!item) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  const allowEdit = item.profileId !== undefined;

  return (
    <Container fluid>
      <Helmet>
        <title>{item.title} - Bazarr (Movies)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.AsyncButton
            icon={faSync}
            promise={() =>
              MoviesApi.action({ action: "scan-disk", radarrid: item.radarrId })
            }
          >
            Scan Disk
          </ContentHeader.AsyncButton>
          <ContentHeader.AsyncButton
            icon={faSearch}
            disabled={item.profileId === null}
            promise={() =>
              MoviesApi.action({
                action: "search-missing",
                radarrid: item.radarrId,
              })
            }
          >
            Search
          </ContentHeader.AsyncButton>
          <ContentHeader.Button
            icon={faUser}
            disabled={item.profileId === null}
            onClick={() => showModal<Item.Movie>("manual-search", item)}
          >
            Manual
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faHistory}
            onClick={() => showModal("history", item)}
          >
            History
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faToolbox}
            onClick={() => showModal("tools", [item])}
          >
            Tools
          </ContentHeader.Button>
        </ContentHeader.Group>

        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={!allowEdit || item.profileId === null}
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload", item)}
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
        <Table movie={item} profile={profile}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(form) => MoviesApi.modify(form)}
      ></ItemEditorModal>
      <SubtitleToolModal modalKey="tools" size="lg"></SubtitleToolModal>
      <MovieHistoryModal modalKey="history" size="lg"></MovieHistoryModal>
      <MovieUploadModal modalKey="upload" size="lg"></MovieUploadModal>
      <ManualSearchModal
        modalKey="manual-search"
        onSelect={download}
      ></ManualSearchModal>
    </Container>
  );
};

export default withRouter(MovieDetailView);
