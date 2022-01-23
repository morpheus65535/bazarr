import { useIsRadarrEnabled, useIsSonarrEnabled } from "@/modules/redux/hooks";
import React, { FunctionComponent } from "react";
import { Navigate } from "react-router-dom";

const Redirector: FunctionComponent = () => {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();

  let path = "/settings";
  if (sonarr) {
    path = "/series";
  } else if (radarr) {
    path = "/movies";
  }

  return <Navigate to={path}></Navigate>;
};

export default Redirector;
