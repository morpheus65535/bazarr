import React, { FunctionComponent, useEffect } from "react";
import { connect } from "react-redux";
import { Route, Switch } from "react-router-dom";
import Movie from ".";
import { movieUpdateInfoAll } from "../@redux/actions";
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

export default connect(null, { update: movieUpdateInfoAll })(Router);
