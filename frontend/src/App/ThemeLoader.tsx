import { useCallback, useEffect, useRef } from "react";
import { MantineColorScheme, useMantineColorScheme } from "@mantine/core";
import { useSystemSettings } from "@/apis/hooks";

const ThemeProvider = () => {
  const { setColorScheme } = useMantineColorScheme();

  const settings = useSystemSettings();

  const settingsColorScheme = settings.data?.general
    .theme as MantineColorScheme;

  const setScheme = useCallback(
    (colorScheme: MantineColorScheme) => {
      setColorScheme(colorScheme);
    },
    [setColorScheme],
  );

  // Tracks the last scheme applied to Mantine so the settings value is only
  // re-applied when it actually changes.
  const appliedScheme = useRef<MantineColorScheme | null>(null);

  useEffect(() => {
    if (!settingsColorScheme) {
      return;
    }

    if (appliedScheme.current === settingsColorScheme) {
      return;
    }

    appliedScheme.current = settingsColorScheme;
    setScheme(settingsColorScheme);
  }, [settingsColorScheme, setScheme]);

  return <></>;
};

export default ThemeProvider;
