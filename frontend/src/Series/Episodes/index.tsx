import React from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { connect } from "react-redux";

import {
  faSync,
  faSearch,
  faCloudUploadAlt,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { updateEpisodeList } from "../../redux/actions/series";

import ContentHeader, {
  ContentHeaderButton,
  ContentHeaderGroup,
} from "../../components/ContentHeader";
import ItemOverview from "../../components/ItemOverview";
import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Series[]>;
  updateEpisodeList: (id: number) => void;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesList } = series;
  return {
    seriesList,
  };
}

class SeriesEpisodesView extends React.Component<Props> {
  componentDidMount() {
    const { id } = this.props.match.params;
    this.props.updateEpisodeList(Number.parseInt(id));
  }
  render() {
    const list = this.props.seriesList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.sonarrSeriesId === Number.parseInt(id));

    const details = [
      item?.audio_language.name,
      item?.mapped_path,
      `${item?.episodeFileCount} files`,
      item?.seriesType,
      item?.tags,
    ];

    if (item) {
      return (
        <div>
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
              <ContentHeaderButton iconProps={{ icon: faWrench }}>
                Edit Series
              </ContentHeaderButton>
            </ContentHeaderGroup>
          </ContentHeader>
          <ItemOverview item={item} details={details}></ItemOverview>
          <Table></Table>
        </div>
      );
    } else {
      return <div></div>;
    }
  }
}

export default withRouter(
  connect(mapStateToProps, { updateEpisodeList })(SeriesEpisodesView)
);
