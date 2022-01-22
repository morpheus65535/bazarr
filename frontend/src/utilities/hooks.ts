import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDidUpdate, useMediaMatch } from "rooks";

export function useGotoHomepage() {
  const navigate = useNavigate();
  return useCallback(() => navigate("/"), [navigate]);
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
