import React from "react";
import { connect } from "react-redux";
import { RouteComponentProps, withRouter } from "react-router-dom";

import {
  faSync,
  faHistory,
  faToolbox,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { Container } from "react-bootstrap";

import ContentHeader, {
  ContentHeaderButton,
  ContentHeaderGroup,
} from "../../components/ContentHeader";
import ItemOverview from "../../components/ItemOverview";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  movieList: AsyncState<Movie[]>;
}

function mapStateToProps({ movie }: StoreState) {
  const { movieList } = movie;
  return {
    movieList,
  };
}

class MovieDetailView extends React.Component<Props> {
  render() {
    const list = this.props.movieList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.radarrId === Number.parseInt(id));

    const details = [item?.audio_language.name, item?.mapped_path, item?.tags]

    if (item) {
      return (
        <Container fluid className="p-0">
          <ContentHeader>
            <ContentHeaderGroup pos="start">
              <ContentHeaderButton iconProps={{ icon: faSync }}>
                Scan Disk
              </ContentHeaderButton>
              <ContentHeaderButton iconProps={{ icon: faHistory }}>
                History
              </ContentHeaderButton>
              <ContentHeaderButton iconProps={{ icon: faToolbox }}>
                Tools
              </ContentHeaderButton>
            </ContentHeaderGroup>
            <ContentHeaderGroup pos="end">
              <ContentHeaderButton iconProps={{ icon: faWrench }}>
                Edit Movie
              </ContentHeaderButton>
            </ContentHeaderGroup>
          </ContentHeader>
          <ItemOverview item={item} details={details}></ItemOverview>
        </Container>
      );
    } else {
      return <div></div>;
    }
  }
}

export default withRouter(connect(mapStateToProps)(MovieDetailView));
