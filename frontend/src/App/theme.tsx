import {
  ColorScheme,
  ColorSchemeProvider,
  MantineProvider,
  MantineThemeOverride,
} from "@mantine/core";
import { useColorScheme } from "@mantine/hooks";
import { FunctionComponent, useCallback, useEffect, useState } from "react";

const theme: MantineThemeOverride = {
  fontFamily: [
    "Roboto",
    "open sans",
    "Helvetica Neue",
    "Helvetica",
    "Arial",
    "sans-serif",
  ],
  colors: {
    brand: [
      "#F8F0FC",
      "#F3D9FA",
      "#EEBEFA",
      "#E599F7",
      "#DA77F2",
      "#CC5DE8",
      "#BE4BDB",
      "#AE3EC9",
      "#9C36B5",
      "#862E9C",
    ],
  },
  primaryColor: "brand",
};

function useAutoColorScheme() {
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useState(preferredColorScheme);

  // automatically switch dark/light theme
  useEffect(() => {
    setColorScheme(preferredColorScheme);
  }, [preferredColorScheme]);

  const toggleColorScheme = useCallback((value?: ColorScheme) => {
    setColorScheme((scheme) => value || (scheme === "dark" ? "light" : "dark"));
  }, []);

  return { colorScheme, setColorScheme, toggleColorScheme };
}

const ThemeProvider: FunctionComponent = ({ children }) => {
  const { colorScheme, toggleColorScheme } = useAutoColorScheme();

  return (
    <ColorSchemeProvider
      colorScheme={colorScheme}
      toggleColorScheme={toggleColorScheme}
    >
      <MantineProvider
        withGlobalStyles
        withNormalizeCSS
        theme={{ colorScheme, ...theme }}
        emotionOptions={{ key: "bazarr" }}
      >
        {children}
      </MantineProvider>
    </ColorSchemeProvider>
  );
};

export default ThemeProvider;
