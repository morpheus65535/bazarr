import React from "react";
import { connect } from "react-redux";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { Helmet } from "react-helmet";

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
import EditItemModal from "../../components/EditItemModal";

import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  movieList: AsyncState<Movie[]>;
}

interface State {
  editMovie: boolean;
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
  render() {
    const list = this.props.movieList.items;
    const { id } = this.props.match.params;
    const item = list.find((val) => val.radarrId === Number.parseInt(id));

    const { editMovie } = this.state;

    const details = [item?.audio_language.name, item?.mapped_path, item?.tags];

    if (item) {
      const header = (
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
            <ContentHeaderButton
              iconProps={{ icon: faWrench }}
              onClick={this.onEditMovieClick.bind(this)}
            >
              Edit Movie
            </ContentHeaderButton>
          </ContentHeaderGroup>
        </ContentHeader>
      );
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
        </Container>
      );
    } else {
      return <div></div>;
    }
  }
}

export default withRouter(connect(mapStateToProps)(MovieDetailView));
