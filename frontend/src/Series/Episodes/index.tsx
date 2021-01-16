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
  LoadingOverlay,
} from "../../Components";

import { SeriesApi } from "../../apis";

import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Series[]>;
  updateEpisodeList: (id: number) => void;
}

interface State {
  modal: string;
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
      modal: "",
    };
  }
  componentDidMount() {
    const { id } = this.props.match.params;
    this.props.updateEpisodeList(Number.parseInt(id));
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
    const list = this.props.seriesList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.sonarrSeriesId === Number.parseInt(id));

    const { updateEpisodeList } = this.props;

    const { modal } = this.state;

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
          <ContentHeaderButton icon={faSync}>Scan Disk</ContentHeaderButton>
          <ContentHeaderButton icon={faSearch}>Search</ContentHeaderButton>
        </ContentHeaderGroup>
        <ContentHeaderGroup pos="end">
          <ContentHeaderButton icon={faCloudUploadAlt}>
            Upload
          </ContentHeaderButton>
          <ContentHeaderButton
            icon={faWrench}
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
          {header}
          <Row>
            <ItemOverview item={item} details={details}></ItemOverview>
          </Row>
          <Row>
            <Table id={id}></Table>
          </Row>
          <ItemEditorModal
            show={modal === "edit"}
            title={item.title}
            item={item}
            onClose={this.closeModal.bind(this)}
            submit={(form) => SeriesApi.modify(item.sonarrSeriesId, form)}
            onSuccess={() => {
              this.closeModal();
              // TODO: Websocket
              updateEpisodeList(item.sonarrSeriesId);
            }}
          ></ItemEditorModal>
        </Container>
      );
    } else {
      return <LoadingOverlay></LoadingOverlay>;
    }
  }
}

export default withRouter(
  connect(mapStateToProps, { updateEpisodeList })(SeriesEpisodesView)
);
