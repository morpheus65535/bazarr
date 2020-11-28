import React from "react";
import { connect } from "react-redux"
import { RouteComponentProps, withRouter } from "react-router-dom";

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
      return <div>{id}</div>;
    } else {
      return <div></div>;
    }
  }
}

export default withRouter(connect(mapStateToProps)(MovieDetailView))
