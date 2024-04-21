import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import { createTheme, MantineProvider } from "@mantine/core";
import { FunctionComponent, PropsWithChildren } from "react";
import ThemeLoader from "@/App/ThemeLoader";

const themeProvider = createTheme({
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
});

const ThemeProvider: FunctionComponent<PropsWithChildren> = ({ children }) => {
  return (
    <MantineProvider theme={themeProvider} defaultColorScheme="auto">
      <ThemeLoader />
      {children}
    </MantineProvider>
  );
};

export default ThemeProvider;
