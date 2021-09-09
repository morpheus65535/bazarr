import { FunctionComponent } from "react";
import { Redirect } from "react-router-dom";
import { useIsMoviesEnabled, useIsSeriesEnabled } from "../@redux/hooks";

const RootRedirect: FunctionComponent = () => {
  const sonarr = useIsSeriesEnabled();
  const radarr = useIsMoviesEnabled();

  let path = "/settings";
  if (sonarr) {
    path = "/series";
  } else if (radarr) {
    path = "movies";
  }

  return <Redirect to={path}></Redirect>;
};

export default RootRedirect;
