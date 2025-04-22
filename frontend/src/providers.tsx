import { FunctionComponent, PropsWithChildren } from "react";
import { Notifications } from "@mantine/notifications";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import queryClient from "@/apis/queries";
import ThemeProvider from "@/App/ThemeProvider";
import { ModalsProvider } from "@/modules/modals";
import { Environment } from "./utilities";
import "@fontsource/roboto/300.css";

export const AllProviders: FunctionComponent<PropsWithChildren> = ({
  children,
}) => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ModalsProvider>
          <Notifications position="bottom-left" limit={5} />
          {/* c8 ignore next 3 */}
          {Environment.queryDev && <ReactQueryDevtools initialIsOpen={false} />}
          {children}
        </ModalsProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};
