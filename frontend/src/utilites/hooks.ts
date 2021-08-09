import { useCallback, useMemo } from "react";
import { useHistory } from "react-router";
import { getBaseUrl } from ".";

export function useBaseUrl(slash: boolean = false) {
  return useMemo(() => getBaseUrl(slash), [slash]);
}

export function useGotoHomepage() {
  const history = useHistory();
  return useCallback(() => history.push("/"), [history]);
}

export function useCanUpdateInject() {
  if (process.env.NODE_ENV !== "production") {
    return process.env["REACT_APP_CAN_UPDATE"] === "true";
  } else {
    return window.Bazarr.canUpdate;
  }
}

export function useHasUpdateInject() {
  if (process.env.NODE_ENV !== "production") {
    return process.env["REACT_APP_HAS_UPDATE"] === "true";
  } else {
    return window.Bazarr.hasUpdate;
  }
}
