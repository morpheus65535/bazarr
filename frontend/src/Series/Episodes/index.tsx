import React from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";

import { connect } from "react-redux";

import {
  faSync,
  faSearch,
  faCloudUploadAlt,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import {
  CommonHeader,
  CommonHeaderBtn,
  CommonHeaderGroup,
} from "../../components/CommonHeader";
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
          <CommonHeader>
            <CommonHeaderGroup dir="start">
              <CommonHeaderBtn iconProps={{ icon: faSync }}>
                Scan Disk
              </CommonHeaderBtn>
              <CommonHeaderBtn iconProps={{ icon: faSearch }}>
                Search
              </CommonHeaderBtn>
            </CommonHeaderGroup>
            <CommonHeaderGroup dir="end">
              <CommonHeaderBtn iconProps={{ icon: faCloudUploadAlt }}>
                Upload
              </CommonHeaderBtn>
              <CommonHeaderBtn iconProps={{ icon: faWrench }}>
                Edit Series
              </CommonHeaderBtn>
            </CommonHeaderGroup>
          </CommonHeader>
          <Detail series={item}></Detail>
        </div>
      );
    } else {
      return <div></div>;
    }
  }
}

export default withRouter(connect(mapStateToProps)(SeriesEpisodesView));
