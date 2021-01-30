import React, { FunctionComponent } from "react";
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
import { MoviesApi, ProvidersApi } from "../../apis";
import { movieUpdateInfoAll } from "../../@redux/actions";
import { ManualSearchModal } from "../../components/modals/ManualSearchModal";

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
          <ContentHeader.Button
            icon={faUser}
            onClick={() => showModal<Movie>("manual-search", item)}
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
            disabled={!allowEdit}
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
        <Table movie={item}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(item, form) =>
          MoviesApi.modify({
            radarrid: [(item as Movie).radarrId],
            profileid: [form.profileid],
          })
        }
        onSuccess={() => update(id)}
      ></ItemEditorModal>
      <SubtitleToolModal modalKey="tools" size="lg"></SubtitleToolModal>
      <MovieHistoryModal modalKey="history" size="lg"></MovieHistoryModal>
      <MovieUploadModal modalKey="upload" size="lg"></MovieUploadModal>
      <ManualSearchModal
        modalKey="manual-search"
        onDownload={() => update(item.radarrId)}
        onSelect={(item, result) => {
          item = item as Movie;
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

export default withRouter(
  connect(mapStateToProps, { update: movieUpdateInfoAll })(MovieDetailView)
);
