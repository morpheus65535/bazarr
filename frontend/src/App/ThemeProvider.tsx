import { FunctionComponent, PropsWithChildren } from "react";
import {
  ActionIcon,
  Badge,
  Button,
  createTheme,
  MantineProvider,
  Pagination,
} from "@mantine/core";
import ThemeLoader from "@/App/ThemeLoader";
import "@mantine/core/styles.layer.css";
import "@mantine/notifications/styles.layer.css";
import styleVars from "@/assets/_variables.module.scss";
import actionIconClasses from "@/assets/action_icon.module.scss";
import badgeClasses from "@/assets/badge.module.scss";
import buttonClasses from "@/assets/button.module.scss";
import paginationClasses from "@/assets/pagination.module.scss";

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
  components: {
    ActionIcon: ActionIcon.extend({
      classNames: actionIconClasses,
    }),
    Badge: Badge.extend({
      classNames: badgeClasses,
    }),
    Button: Button.extend({
      classNames: buttonClasses,
    }),
    Pagination: Pagination.extend({
      classNames: paginationClasses,
    }),
  },
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
