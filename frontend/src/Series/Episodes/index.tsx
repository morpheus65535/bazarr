import React from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { connect } from "react-redux";

import { Container } from "react-bootstrap"

import {
  faSync,
  faSearch,
  faCloudUploadAlt,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { updateEpisodeList } from "../../@redux/actions/series";

import ContentHeader, {
  ContentHeaderButton,
  ContentHeaderGroup,
} from "../../components/ContentHeader";
import ItemOverview from "../../components/ItemOverview";
import Table from "./table";
import EditItemModal from "../../components/EditItemModal";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Series[]>;
  updateEpisodeList: (id: number) => void;
}

interface State {
  editSeries: boolean;
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
      editSeries: false,
    };
  }
  componentDidMount() {
    const { id } = this.props.match.params;
    this.props.updateEpisodeList(Number.parseInt(id));
  }

  onEditSeriesClick() {
    this.setState({
      ...this.state,
      editSeries: true,
    });
  }

  onEditSeriesClose() {
    this.setState({
      ...this.state,
      editSeries: false,
    });
  }
  render() {
    const list = this.props.seriesList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.sonarrSeriesId === Number.parseInt(id));

    const { editSeries } = this.state;

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
            onClick={this.onEditSeriesClick.bind(this)}
          >
            Edit Series
          </ContentHeaderButton>
        </ContentHeaderGroup>
      </ContentHeader>
    );

    if (item) {
      return (
        <Container fluid className="p-0">
          {header}
          <ItemOverview item={item} details={details}></ItemOverview>
          <Table id={id}></Table>
          <EditItemModal
            item={editSeries ? item : undefined}
            onClose={this.onEditSeriesClose.bind(this)}
          ></EditItemModal>
        </Container>
      );
    } else {
      return <div></div>;
    }
  }
}

export default withRouter(
  connect(mapStateToProps, { updateEpisodeList })(SeriesEpisodesView)
);
