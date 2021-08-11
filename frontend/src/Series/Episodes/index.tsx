import {
  faAdjust,
  faBriefcase,
  faCloudUploadAlt,
  faHdd,
  faSearch,
  faSync,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useMemo, useState } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Redirect, RouteComponentProps, withRouter } from "react-router-dom";
import { useEpisodesBy, useProfileBy, useSerieBy } from "../../@redux/hooks";
import { SeriesApi } from "../../apis";
import {
  ContentHeader,
  ItemEditorModal,
  LoadingIndicator,
  SeriesUploadModal,
  useShowModal,
} from "../../components";
import ItemOverview from "../../generic/ItemOverview";
import { RouterEmptyPath } from "../../special-pages/404";
import { useOnLoadedOnce } from "../../utilites";
import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {}

const SeriesEpisodesView: FunctionComponent<Props> = (props) => {
  const { match } = props;
  const id = Number.parseInt(match.params.id);
  const [series] = useSerieBy(id);
  const [episodes] = useEpisodesBy(id);
  const serie = series.content;

  const available = episodes.content.length !== 0;

  const details = useMemo(
    () => [
      {
        icon: faHdd,
        text: `${serie?.episodeFileCount} files`,
      },
      {
        icon: faAdjust,
        text: serie?.seriesType ?? "",
      },
    ],
    [serie]
  );

  const showModal = useShowModal();

  const [valid, setValid] = useState(true);

  useOnLoadedOnce(() => {
    if (series.content === null) {
      setValid(false);
    }
  }, series);

  const profile = useProfileBy(series.content?.profileId);

  if (isNaN(id) || !valid) {
    return <Redirect to={RouterEmptyPath}></Redirect>;
  }

  if (!serie) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <Container fluid>
      <Helmet>
        <title>{serie.title} - Bazarr (Series)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.AsyncButton
            icon={faSync}
            disabled={!available}
            promise={() =>
              SeriesApi.action({ action: "scan-disk", seriesid: id })
            }
          >
            Scan Disk
          </ContentHeader.AsyncButton>
          <ContentHeader.AsyncButton
            icon={faSearch}
            promise={() =>
              SeriesApi.action({ action: "search-missing", seriesid: id })
            }
            disabled={
              serie.episodeFileCount === 0 ||
              serie.profileId === null ||
              !available
            }
          >
            Search
          </ContentHeader.AsyncButton>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={serie.episodeFileCount === 0 || !available}
            icon={faBriefcase}
            onClick={() => showModal("tools", episodes.content)}
          >
            Tools
          </ContentHeader.Button>
          <ContentHeader.Button
            disabled={
              serie.episodeFileCount === 0 ||
              serie.profileId === null ||
              !available
            }
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload", serie)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            onClick={() => showModal("edit", serie)}
          >
            Edit Series
          </ContentHeader.Button>
        </ContentHeader.Group>
      </ContentHeader>
      <Row>
        <ItemOverview item={serie} details={details}></ItemOverview>
      </Row>
      <Row>
        <Table episodes={episodes} profile={profile}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(form) => SeriesApi.modify(form)}
      ></ItemEditorModal>
      <SeriesUploadModal
        modalKey="upload"
        episodes={episodes.content}
      ></SeriesUploadModal>
    </Container>
  );
};

export default withRouter(SeriesEpisodesView);
