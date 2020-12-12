import React from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { Container, Row } from "react-bootstrap";

import {
  faSync,
  faSearch,
  faCloudUploadAlt,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { updateEpisodeList } from "../../@redux/actions";

import {
  ContentHeader,
  ContentHeaderButton,
  ContentHeaderGroup,
  ItemOverview,
  ItemEditorModal,
  LoadingIndicator,
} from "../../components";

import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Series[]>;
  updateEpisodeList: (id: number) => void;
}

interface State {
  liveModal: string;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesList } = series;
  return {
    seriesList,
  };
}

class SeriesEpisodesView extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      liveModal: "",
    };
  }
  componentDidMount() {
    const { id } = this.props.match.params;
    this.props.updateEpisodeList(Number.parseInt(id));
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
    const list = this.props.seriesList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.sonarrSeriesId === Number.parseInt(id));

    const { liveModal } = this.state;

    const details = [
      item?.audio_language.name,
      item?.mapped_path,
      `${item?.episodeFileCount} files`,
      item?.seriesType,
      item?.tags,
    ];

    const header = (
      <ContentHeader>
        <ContentHeaderGroup pos="start">
          <ContentHeaderButton iconProps={{ icon: faSync }}>
            Scan Disk
          </ContentHeaderButton>
          <ContentHeaderButton iconProps={{ icon: faSearch }}>
            Search
          </ContentHeaderButton>
        </ContentHeaderGroup>
        <ContentHeaderGroup pos="end">
          <ContentHeaderButton iconProps={{ icon: faCloudUploadAlt }}>
            Upload
          </ContentHeaderButton>
          <ContentHeaderButton
            iconProps={{ icon: faWrench }}
            onClick={() => this.showModal("edit")}
          >
            Edit Series
          </ContentHeaderButton>
        </ContentHeaderGroup>
      </ContentHeader>
    );

    if (item) {
      return (
        <Container fluid>
          <Helmet>
            <title>{item.title} - Bazarr (Series)</title>
          </Helmet>
          <Row>{header}</Row>
          <Row>
            <ItemOverview item={item} details={details}></ItemOverview>
          </Row>
          <Row>
            <Table id={id}></Table>
          </Row>
          <ItemEditorModal
            item={liveModal === "edit" ? item : undefined}
            onClose={this.closeModal.bind(this)}
          ></ItemEditorModal>
        </Container>
      );
    } else {
      return <LoadingIndicator></LoadingIndicator>;
    }
  }
}

export default withRouter(
  connect(mapStateToProps, { updateEpisodeList })(SeriesEpisodesView)
);
