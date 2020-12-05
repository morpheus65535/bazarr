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

import { Container } from "react-bootstrap";

import {
  ContentHeader,
  ContentHeaderButton,
  ContentHeaderGroup,
  EditItemModal,
  ItemOverview,
  LoadingOverlay,
  ActionModal,
  TabElement,
} from "../../components";

import Table from "./table";
import ToolTable from "./ToolTable";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  movieList: AsyncState<Movie[]>;
}

interface State {
  editMovie: boolean;
  actionModalShow: boolean;
  actionModalKey?: string;
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
      editMovie: false,
      actionModalShow: false,
      actionModalKey: undefined,
    };
  }
  onEditMovieClick() {
    this.setState({
      ...this.state,
      editMovie: true,
    });
  }
  onEditMovieClose() {
    this.setState({
      ...this.state,
      editMovie: false,
    });
  }
  onActionModalClick(key?: string) {
    this.setState({
      ...this.state,
      actionModalShow: true,
      actionModalKey: key,
    });
  }
  onActionModalClose() {
    this.setState({
      ...this.state,
      actionModalShow: false,
      actionModalKey: undefined,
    });
  }
  render() {
    const list = this.props.movieList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.radarrId === Number.parseInt(id));

    const { editMovie, actionModalShow, actionModalKey } = this.state;

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
              onClick={() => this.onActionModalClick("tools")}
            >
              Tools
            </ContentHeaderButton>
          </ContentHeaderGroup>
          <ContentHeaderGroup pos="end">
            <ContentHeaderButton
              iconProps={{ icon: faWrench }}
              onClick={this.onEditMovieClick.bind(this)}
            >
              Edit Movie
            </ContentHeaderButton>
          </ContentHeaderGroup>
        </ContentHeader>
      );

      const actionTabs: TabElement[] = [
        {
          event: "tools",
          title: "Tools",
          element: <ToolTable subtitles={item.subtitles}></ToolTable>,
        },
      ];

      return (
        <Container fluid className="p-0">
          <Helmet>
            <title>{item.title} - Bazarr (Movies)</title>
          </Helmet>
          {header}
          <ItemOverview item={item} details={details}></ItemOverview>
          <Table movie={item}></Table>
          <EditItemModal
            item={editMovie ? item : undefined}
            onClose={this.onEditMovieClose.bind(this)}
          ></EditItemModal>
          <ActionModal
            title={item.title}
            show={actionModalShow}
            active={actionModalKey}
            close={this.onActionModalClose.bind(this)}
            tabs={actionTabs}
          ></ActionModal>
        </Container>
      );
    } else {
      return <LoadingOverlay></LoadingOverlay>;
    }
  }
}

export default withRouter(connect(mapStateToProps)(MovieDetailView));
