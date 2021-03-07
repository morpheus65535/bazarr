import {
  faCloudUploadAlt,
  faHistory,
  faSearch,
  faSync,
  faToolbox,
  faUser,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { useMovieBy } from "../../@redux/hooks";
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
import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {}

const MovieDetailView: FunctionComponent<Props> = ({ match }) => {
  const id = Number.parseInt(match.params.id);
  const [movie, update] = useMovieBy(id);
  const item = movie.items;

  const showModal = useShowModal();

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
            onSuccess={update}
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
            onSuccess={update}
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
            onClick={() => showModal("tools", item)}
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
        <Table movie={item} update={update}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(form) => MoviesApi.modify(form)}
        onSuccess={update}
      ></ItemEditorModal>
      <SubtitleToolModal modalKey="tools" size="lg"></SubtitleToolModal>
      <MovieHistoryModal modalKey="history" size="lg"></MovieHistoryModal>
      <MovieUploadModal modalKey="upload" size="lg"></MovieUploadModal>
      <ManualSearchModal
        modalKey="manual-search"
        onDownload={update}
        onSelect={(item, result) => {
          item = item as Item.Movie;
          const {
            language,
            hearing_impaired,
            forced,
            provider,
            subtitle,
          } = result;
          return ProvidersApi.downloadMovieSubtitle(item.radarrId, {
            language,
            hi: hearing_impaired,
            forced,
            provider,
            subtitle,
          });
        }}
      ></ManualSearchModal>
    </Container>
  );
};

export default withRouter(MovieDetailView);
