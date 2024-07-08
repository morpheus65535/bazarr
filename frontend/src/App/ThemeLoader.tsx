import { useCallback, useEffect, useState } from "react";
import { MantineColorScheme, useMantineColorScheme } from "@mantine/core";
import { useSystemSettings } from "@/apis/hooks";

const ThemeProvider = () => {
  const [localScheme, setLocalScheme] = useState<MantineColorScheme | null>(
    null,
  );
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

  useEffect(() => {
    if (!settingsColorScheme) {
      return;
    }

    if (localScheme === settingsColorScheme) {
      return;
    }

    setScheme(settingsColorScheme);
    setLocalScheme(settingsColorScheme);
  }, [settingsColorScheme, setScheme, localScheme]);

  return <></>;
};

export default ThemeProvider;
