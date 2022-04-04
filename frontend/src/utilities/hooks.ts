import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDidUpdate } from "rooks";

export function useGotoHomepage() {
  const navigate = useNavigate();
  return useCallback(() => navigate("/"), [navigate]);
}

export function useIsArrayExtended(arr: unknown[]) {
  const [size, setSize] = useState(arr.length);
  const [isExtended, setExtended] = useState(arr.length !== 0);

  useDidUpdate(() => {
    setExtended(arr.length > size);
    setSize(arr.length);
  }, [arr.length]);

  return isExtended;
}
