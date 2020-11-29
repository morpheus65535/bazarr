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

import {
  CommonHeader,
  CommonHeaderBtn,
  CommonHeaderGroup,
} from "../../components/CommonHeader";

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

    if (item) {
      return (
        <Container fluid className="p-0">
          <CommonHeader>
            <CommonHeaderGroup dir="start">
              <CommonHeaderBtn iconProps={{ icon: faSync }}>
                Scan Disk
              </CommonHeaderBtn>
              <CommonHeaderBtn iconProps={{ icon: faHistory }}>
                History
              </CommonHeaderBtn>
              <CommonHeaderBtn iconProps={{ icon: faToolbox }}>
                Tools
              </CommonHeaderBtn>
            </CommonHeaderGroup>
            <CommonHeaderGroup dir="end">
              <CommonHeaderBtn iconProps={{ icon: faWrench }}>
                Edit Movie
              </CommonHeaderBtn>
            </CommonHeaderGroup>
          </CommonHeader>
        </Container>
      );
    } else {
      return <div></div>;
    }
  }
}

export default withRouter(connect(mapStateToProps)(MovieDetailView));
