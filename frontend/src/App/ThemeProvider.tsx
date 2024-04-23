import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import { createTheme, MantineProvider } from "@mantine/core";
import { FunctionComponent, PropsWithChildren } from "react";
import ThemeLoader from "@/App/ThemeLoader";
import styleVars from "@/_variables.module.scss";

const themeProvider = createTheme({
  fontFamily: "Roboto, open sans, Helvetica Neue, Helvetica, Arial, sans-serif",
  colors: {
    brand: [
      styleVars.colorBrand0,
      styleVars.colorBrand1,
      styleVars.colorBrand2,
      styleVars.colorBrand3,
      styleVars.colorBrand4,
      styleVars.colorBrand5,
      styleVars.colorBrand6,
      styleVars.colorBrand7,
      styleVars.colorBrand8,
      styleVars.colorBrand9,
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
