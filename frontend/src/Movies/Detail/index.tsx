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
  LoadingIndicator,
  SubtitleToolModal,
} from "../../Components";

import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  movieList: AsyncState<Movie[]>;
}

interface State {
  liveModal: string;
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
      liveModal: "",
    };
  }

  showModal(key: string) {
    this.setState({
      ...this.state,
      liveModal: key,
    });
  }

  closeModal() {
    this.setState({
      ...this.state,
      liveModal: "",
    });
  }

  render() {
    const list = this.props.movieList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.radarrId === Number.parseInt(id));

    const { liveModal } = this.state;

    const details = [item?.audio_language.name, item?.mapped_path, item?.tags];

    if (item) {
      const allowEdit = item.languages instanceof Array;

      const editButton = (
        <React.Fragment>
          <ContentHeaderButton iconProps={{ icon: faSearch }}>
            Search
          </ContentHeaderButton>
          <ContentHeaderButton iconProps={{ icon: faUser }}>
            Manual
          </ContentHeaderButton>
          <ContentHeaderButton iconProps={{ icon: faCloudUploadAlt }}>
            Upload
          </ContentHeaderButton>
        </React.Fragment>
      );

      const header = (
        <ContentHeader>
          <ContentHeaderGroup pos="start">
            <ContentHeaderButton iconProps={{ icon: faSync }}>
              Scan Disk
            </ContentHeaderButton>
            {allowEdit && editButton}
            <ContentHeaderButton
              iconProps={{ icon: faHistory }}
              // onClick={() => this.onActionModalClick("history")}
            >
              History
            </ContentHeaderButton>
            <ContentHeaderButton
              iconProps={{ icon: faToolbox }}
              onClick={() => this.showModal("tools")}
            >
              Tools
            </ContentHeaderButton>
          </ContentHeaderGroup>
          <ContentHeaderGroup pos="end">
            <ContentHeaderButton
              iconProps={{ icon: faWrench }}
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
          <Row>{header}</Row>
          <Row>
            <ItemOverview item={item} details={details}></ItemOverview>
          </Row>
          <Row>
            <Table movie={item}></Table>
          </Row>
          <ItemEditorModal
            item={liveModal === "edit" ? item : undefined}
            onClose={this.closeModal.bind(this)}
          ></ItemEditorModal>
          <SubtitleToolModal
            item={liveModal === "tools" ? item : undefined}
            subtitles={item.subtitles}
            onClose={this.closeModal.bind(this)}
          ></SubtitleToolModal>
        </Container>
      );
    } else {
      return <LoadingIndicator></LoadingIndicator>;
    }
  }
}

export default withRouter(connect(mapStateToProps)(MovieDetailView));
