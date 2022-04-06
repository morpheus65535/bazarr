import queryClient from "@/apis/queries";
import store from "@/modules/redux/store";
// TODO
// import "@/styles/index.scss";
import "@fontsource/roboto/300.css";
import {
  ColorScheme,
  ColorSchemeProvider,
  MantineProvider,
  TypographyStylesProvider,
} from "@mantine/core";
import { useColorScheme } from "@mantine/hooks";
import { StrictMode, useCallback, useEffect, useState } from "react";
import { QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import { Provider } from "react-redux";
import { useRoutes } from "react-router-dom";
import { Router, useRouteItems } from "./Router";
import Theme from "./theme";
import { Environment } from "./utilities";

const RouteApp = () => {
  const items = useRouteItems();

  return useRoutes(items);
};

export const Main = () => {
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useState(preferredColorScheme);

  // automatically switch dark/light theme
  useEffect(() => {
    setColorScheme(preferredColorScheme);
  }, [preferredColorScheme]);

  const toggleColorScheme = useCallback((value?: ColorScheme) => {
    setColorScheme((scheme) => value || (scheme === "dark" ? "light" : "dark"));
  }, []);

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ColorSchemeProvider
          colorScheme={colorScheme}
          toggleColorScheme={toggleColorScheme}
        >
          <MantineProvider
            withGlobalStyles
            withNormalizeCSS
            theme={{ colorScheme, ...Theme }}
          >
            <TypographyStylesProvider>
              <Router>
                <StrictMode>
                  {Environment.queryDev && (
                    <ReactQueryDevtools initialIsOpen={false} />
                  )}
                  <RouteApp></RouteApp>
                </StrictMode>
              </Router>
            </TypographyStylesProvider>
          </MantineProvider>
        </ColorSchemeProvider>
      </QueryClientProvider>
    </Provider>
  );
};
