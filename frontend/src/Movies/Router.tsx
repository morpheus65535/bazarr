import React, { FunctionComponent } from "react";
import { Route, Switch } from "react-router-dom";
import Movie from ".";
import { useMovies } from "../@redux/hooks";
import { useAutoUpdate } from "../utilites/hooks";
import MovieDetail from "./Detail";

interface Props {}

const Router: FunctionComponent<Props> = () => {
  const [, update] = useMovies();
  useAutoUpdate(update);

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

export default Router;
