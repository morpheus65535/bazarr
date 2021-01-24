import React, { FunctionComponent, useEffect } from "react";
import { Route, Switch } from "react-router-dom";

import { connect } from "react-redux";
import { updateMovieList } from "../@redux/actions";

import Movie from ".";
import MovieDetail from "./Detail";

interface Props {
  update: () => void;
}

const Router: FunctionComponent<Props> = ({ update }) => {
  useEffect(() => update(), [update]);

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
};

export default connect(null, { update: updateMovieList })(Router);
