import {
  faAdjust,
  faCloudUploadAlt,
  faHdd,
  faSearch,
  faSync,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useMemo } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { useEpisodesBy, useSerieBy } from "../../@redux/hooks";
import { SeriesApi } from "../../apis";
import {
  ContentHeader,
  ItemEditorModal,
  LoadingIndicator,
  SeriesUploadModal,
  useShowModal,
} from "../../components";
import ItemOverview from "../../generic/ItemOverview";
import { useAutoUpdate } from "../../utilites";
import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {}

const SeriesEpisodesView: FunctionComponent<Props> = (props) => {
  const { match } = props;
  const id = Number.parseInt(match.params.id);
  const [serie, update] = useSerieBy(id);
  const item = serie.data;

  const [episodes, updateEpisodes] = useEpisodesBy(serie.data?.sonarrSeriesId);
  useAutoUpdate(updateEpisodes);

  const avaliable = episodes.data.length !== 0;

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
          <ContentHeader.AsyncButton
            icon={faSync}
            disabled={!avaliable}
            promise={() =>
              SeriesApi.action({ action: "scan-disk", seriesid: id })
            }
            onSuccess={update}
          >
            Scan Disk
          </ContentHeader.AsyncButton>
          <ContentHeader.AsyncButton
            icon={faSearch}
            promise={() =>
              SeriesApi.action({ action: "search-missing", seriesid: id })
            }
            onSuccess={update}
            disabled={
              item.episodeFileCount === 0 ||
              item.profileId === null ||
              !avaliable
            }
          >
            Search
          </ContentHeader.AsyncButton>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={
              item.episodeFileCount === 0 ||
              item.profileId === null ||
              !avaliable
            }
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload", item)}
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
        <Table episodes={episodes} update={updateEpisodes}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(form) => SeriesApi.modify(form)}
        onSuccess={update}
      ></ItemEditorModal>
      <SeriesUploadModal modalKey="upload"></SeriesUploadModal>
    </Container>
  );
};

export default withRouter(SeriesEpisodesView);
