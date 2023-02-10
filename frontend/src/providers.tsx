import queryClient from "@/apis/queries";
import ThemeProvider from "@/App/theme";
import { ModalsProvider } from "@/modules/modals";
import "@fontsource/roboto/300.css";
import { NotificationsProvider } from "@mantine/notifications";
import { FunctionComponent } from "react";
import { QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import { Router } from "./Router";
import { Environment } from "./utilities";

export const AllProviders: FunctionComponent = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ModalsProvider>
          <NotificationsProvider limit={5}>
            <Router>
              {Environment.queryDev && (
                <ReactQueryDevtools initialIsOpen={false} />
              )}
              {children}
            </Router>
          </NotificationsProvider>
        </ModalsProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};
