import { useEffect, useState } from "react";

export function useOnShow(callback: () => void) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!show) {
      setShow(true);
      callback();
    }
  }, [show]); // eslint-disable-line react-hooks/exhaustive-deps
}

export function useBaseUrl(slash: boolean = false) {
  if (process.env.NODE_ENV === "development") {
    return "/";
  } else {
    let url = window.Bazarr.baseUrl ?? "/";
    if (slash && !url.endsWith("/")) {
      url += "/";
    }
    return url;
  }
}
