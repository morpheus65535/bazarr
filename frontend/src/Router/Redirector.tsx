import { useSystemSettings } from "@/apis/hooks";
import { LoadingOverlay } from "@mantine/core";
import { FunctionComponent, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const Redirector: FunctionComponent = () => {
  const { data } = useSystemSettings();

  const navigate = useNavigate();

  useEffect(() => {
    if (data) {
      const { use_sonarr, use_radarr } = data.general;
      if (use_sonarr) {
        navigate("/series");
      } else if (use_radarr) {
        navigate("/movies");
      } else {
        navigate("/settings/general");
      }
    }
  }, [data, navigate]);

  return <LoadingOverlay visible></LoadingOverlay>;
};

export default Redirector;
