import React from "react";
import { Route, Switch } from "react-router-dom";

import { connect } from "react-redux";
import { updateMovieList } from "../redux/actions/movie";

import Movie from ".";
import MovieDetail from "./Detail";

interface Props {
  updateMovieList: () => void;
}

class Router extends React.Component<Props> {
  componentDidMount() {
    this.props.updateMovieList();
  }
  render(): JSX.Element {
    return (
      <Switch>
        <Route exact path="/movies">
          <Movie></Movie>
        </Route>
        <Route path="/movies/:id">
          <MovieDetail></MovieDetail>
        </Route>
      </Switch>
    );
  }
}

export default connect(null, { updateMovieList })(Router);
