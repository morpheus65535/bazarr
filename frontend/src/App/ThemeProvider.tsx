import {
  ActionIcon,
  AppShell,
  Badge,
  Button,
  createTheme,
  MantineProvider,
} from "@mantine/core";
import { FunctionComponent, PropsWithChildren } from "react";
import ThemeLoader from "@/App/ThemeLoader";
import "@mantine/core/styles.layer.css";
import "@mantine/notifications/styles.layer.css";
import styleVars from "@/assets/_variables.module.scss";
import buttonClasses from "@/assets/button.module.scss";
import actionIconClasses from "@/assets/action_icon.module.scss";
import appShellClasses from "@/assets/app_shell.module.scss";
import badgeClasses from "@/assets/badge.module.scss";

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
    AppShell: AppShell.extend({
      classNames: appShellClasses,
    }),
    Badge: Badge.extend({
      classNames: badgeClasses,
    }),
    Button: Button.extend({
      classNames: buttonClasses,
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
