import { FunctionComponent, useEffect } from "react";
import { useNavigate } from "react-router";
import { LoadingOverlay } from "@mantine/core";
import { useSystemSettings } from "@/apis/hooks";

const Redirector: FunctionComponent = () => {
  const { data } = useSystemSettings();

  const navigate = useNavigate();

  useEffect(() => {
    if (data) {
      const { use_sonarr: useSonarr, use_radarr: useRadarr } = data.general;
      if (useSonarr) {
        navigate("/series");
      } else if (useRadarr) {
        navigate("/movies");
      } else {
        navigate("/settings/general");
      }
    }
  }, [data, navigate]);

  return <LoadingOverlay visible></LoadingOverlay>;
};

export default Redirector;
