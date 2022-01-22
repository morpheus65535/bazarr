import { useIsRadarrEnabled, useIsSonarrEnabled } from "@redux/hooks";
import { FunctionComponent } from "react";
import { Redirect } from "react-router-dom";

const RootRedirect: FunctionComponent = () => {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();

  let path = "/settings";
  if (sonarr) {
    path = "/series";
  } else if (radarr) {
    path = "movies";
  }

  return <Redirect to={path}></Redirect>;
};

export default RootRedirect;
