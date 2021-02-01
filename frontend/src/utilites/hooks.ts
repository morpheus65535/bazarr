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
