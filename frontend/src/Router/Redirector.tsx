import { useEnabledStatus } from "@/modules/redux/hooks";
import React, { FunctionComponent } from "react";
import { Navigate } from "react-router-dom";

const Redirector: FunctionComponent = () => {
  const { sonarr, radarr } = useEnabledStatus();

  let path = "/settings";
  if (sonarr) {
    path = "/series";
  } else if (radarr) {
    path = "/movies";
  }

  return <Navigate to={path}></Navigate>;
};

export default Redirector;
