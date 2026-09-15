import { useState } from "react";

// Runs onChange when key changes, adjusting state during render rather than
// in an effect so there's no extra render.
export const useResetOnChange = (key: string, onChange: () => void) => {
  const [prevKey, setPrevKey] = useState(key);
  if (prevKey !== key) {
    setPrevKey(key);
    onChange();
  }
};
