import React from "react";
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
  LoadingOverlay,
  SubtitleToolModal,
  MovieHistoryModal,
} from "../../Components";

import Table from "./table";
import { MoviesApi } from "../../apis";
import { updateMovieInfo } from "../../@redux/actions";

import { updateAsyncState } from "../../utilites";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  movieList: AsyncState<Movie[]>;
  update: (id: number) => void;
}

interface State {
  modal: string;
  history: AsyncState<MovieHistory[]>;
}

function mapStateToProps({ movie }: StoreState) {
  const { movieList } = movie;
  return {
    movieList,
  };
}

class MovieDetailView extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      modal: "",
      history: {
        updating: true,
        items: [],
      },
    };
  }

  setHistory(history: AsyncState<MovieHistory[]>) {
    this.setState({
      ...this.state,
      history,
    });
  }

  showModal(key: string) {
    this.setState({
      ...this.state,
      modal: key,
    });
  }

  closeModal() {
    this.setState({
      ...this.state,
      modal: "",
    });
  }

  render() {
    const list = this.props.movieList.items;
    const id = Number.parseInt(this.props.match.params.id);
    const item = list.find((val) => val.radarrId === id);

    const { update } = this.props;
    const { modal, history } = this.state;

    const details = [item?.audio_language.name, item?.mapped_path, item?.tags];

    if (item) {
      const allowEdit = item.languages instanceof Array;

      const editButton = (
        <React.Fragment>
          <ContentHeaderButton icon={faSearch}>Search</ContentHeaderButton>
          <ContentHeaderButton icon={faUser}>Manual</ContentHeaderButton>
          <ContentHeaderButton icon={faCloudUploadAlt}>
            Upload
          </ContentHeaderButton>
        </React.Fragment>
      );

      const header = (
        <ContentHeader>
          <ContentHeaderGroup pos="start">
            <ContentHeaderButton icon={faSync}>Scan Disk</ContentHeaderButton>
            {allowEdit && editButton}
            <ContentHeaderButton
              icon={faHistory}
              onClick={() => {
                updateAsyncState(
                  MoviesApi.history(id),
                  this.setHistory.bind(this),
                  []
                );
                this.showModal("history");
              }}
            >
              History
            </ContentHeaderButton>
            <ContentHeaderButton
              icon={faToolbox}
              onClick={() => this.showModal("tools")}
            >
              Tools
            </ContentHeaderButton>
          </ContentHeaderGroup>
          <ContentHeaderGroup pos="end">
            <ContentHeaderButton
              icon={faWrench}
              onClick={() => this.showModal("edit")}
            >
              Edit Movie
            </ContentHeaderButton>
          </ContentHeaderGroup>
        </ContentHeader>
      );

      return (
        <Container fluid>
          <Helmet>
            <title>{item.title} - Bazarr (Movies)</title>
          </Helmet>
          {header}
          <Row>
            <ItemOverview item={item} details={details}></ItemOverview>
          </Row>
          <Row>
            <Table movie={item}></Table>
          </Row>
          <ItemEditorModal
            show={modal === "edit"}
            item={item}
            title={item.title}
            onClose={this.closeModal.bind(this)}
            submit={(form) => MoviesApi.modify(item!.radarrId, form)}
            onSuccess={() => {
              this.closeModal();
              update(id);
            }}
          ></ItemEditorModal>
          <SubtitleToolModal
            show={modal === "tools"}
            title={item.title}
            subtitles={item.subtitles}
            onClose={this.closeModal.bind(this)}
          ></SubtitleToolModal>
          <MovieHistoryModal
            show={modal === "history"}
            title={item.title}
            history={history}
            onClose={this.closeModal.bind(this)}
          ></MovieHistoryModal>
        </Container>
      );
    } else {
      return <LoadingOverlay></LoadingOverlay>;
    }
  }
}

export default withRouter(
  connect(mapStateToProps, { update: updateMovieInfo })(MovieDetailView)
);
