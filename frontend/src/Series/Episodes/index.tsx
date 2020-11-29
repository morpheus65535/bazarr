import React from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";

import { connect } from "react-redux";

import {
  faSync,
  faSearch,
  faCloudUploadAlt,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import ContentHeader, {
  ContentHeaderButton,
  ContentHeaderGroup,
} from "../../components/ContentHeader";
import Detail from "./EpisodeDetail";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Series[]>;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesList } = series;
  return {
    seriesList,
  };
}

class SeriesEpisodesView extends React.Component<Props> {
  render() {
    const list = this.props.seriesList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.sonarrSeriesId === Number.parseInt(id));

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
          <Detail series={item}></Detail>
        </div>
      );
    } else {
      return <div></div>;
    }
  }
}

export default withRouter(connect(mapStateToProps)(SeriesEpisodesView));
