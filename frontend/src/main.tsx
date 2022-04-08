import queryClient from "@/apis/queries";
import ThemeProvider from "@/App/theme";
import { ModalsProvider } from "@/modules/modals";
import "@fontsource/roboto/300.css";
import { NotificationsProvider } from "@mantine/notifications";
import { StrictMode } from "react";
import { QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import { useRoutes } from "react-router-dom";
import { Router, useRouteItems } from "./Router";
import { Environment } from "./utilities";

const RouteApp = () => {
  const items = useRouteItems();

  return useRoutes(items);
};

export const Main = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ModalsProvider>
          <NotificationsProvider limit={5}>
            <Router>
              <StrictMode>
                {Environment.queryDev && (
                  <ReactQueryDevtools initialIsOpen={false} />
                )}
                <RouteApp></RouteApp>
              </StrictMode>
            </Router>
          </NotificationsProvider>
        </ModalsProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};
