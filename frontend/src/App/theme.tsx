import { useSystemSettings } from "@/apis/hooks";
import {
  ColorScheme,
  ColorSchemeProvider,
  createEmotionCache,
  MantineProvider,
  MantineThemeOverride,
} from "@mantine/core";
import { useColorScheme } from "@mantine/hooks";
import {
  FunctionComponent,
  PropsWithChildren,
  useCallback,
  useEffect,
  useState,
} from "react";

const theme: MantineThemeOverride = {
  fontFamily: "Roboto, open sans, Helvetica Neue, Helvetica, Arial, sans-serif",
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
  const settings = useSystemSettings();
  const settingsColorScheme = settings.data?.general.theme;

  let preferredColorScheme: ColorScheme = useColorScheme();
  switch (settingsColorScheme) {
    case "light":
      preferredColorScheme = "light" as ColorScheme;
      break;
    case "dark":
      preferredColorScheme = "dark" as ColorScheme;
      break;
  }

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

const emotionCache = createEmotionCache({ key: "bazarr" });

const ThemeProvider: FunctionComponent<PropsWithChildren> = ({ children }) => {
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
        emotionCache={emotionCache}
      >
        {children}
      </MantineProvider>
    </ColorSchemeProvider>
  );
};

export default ThemeProvider;
