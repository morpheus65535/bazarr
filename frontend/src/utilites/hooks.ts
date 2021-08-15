import { useCallback, useMemo, useState } from "react";
import { useHistory } from "react-router";
import { useDidUpdate } from "rooks";
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

export function useIsArrayExtended(arr: any[]) {
  const [size, setSize] = useState(arr.length);
  const [isExtended, setExtended] = useState(arr.length !== 0);

  useDidUpdate(() => {
    setExtended(arr.length > size);
    setSize(arr.length);
  }, [arr.length]);

  return isExtended;
}
