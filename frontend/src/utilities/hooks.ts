import { useCallback, useState } from "react";
import { useHistory } from "react-router";
import { useDidUpdate, useMediaMatch } from "rooks";

export function useGotoHomepage() {
  const history = useHistory();
  return useCallback(() => history.push("/"), [history]);
}

export function useIsMobile() {
  return useMediaMatch("(max-width: 576px)");
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
