import React, {
  createContext,
  FunctionComponent,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { matchPath, NavLink, RouteObject, useLocation } from "react-router";
import {
  Anchor,
  AppShell,
  Badge,
  Collapse,
  Divider,
  Group,
  MantineColorScheme,
  Stack,
  Text,
  useMantineColorScheme,
} from "@mantine/core";
import {
  faCircleHalfStroke,
  faHeart,
  faMoon,
  faSun,
  IconDefinition,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { QueryKeys } from "@/apis/queries/keys";
import { Action } from "@/components";
import { useNavbar } from "@/contexts/Navbar";
import { CustomRouteObject, Route } from "@/Router/type";
import { useRouteItems } from "@/Router/useRouteItems";
import { BuildKey, pathJoin } from "@/utilities";
import { LOG } from "@/utilities/console";
import styles from "./Navbar.module.scss";

const Selection = createContext<{
  selection: string | null;
  select: (path: string | null) => void;
}>({
  selection: null,
  select: () => {
    LOG("error", "Selection context not initialized");
  },
});

const useSelection = () => useContext(Selection);

const useBadgeValue = (route: Route.Item) => {
  const { badge, children } = route;
  return useMemo(() => {
    if (typeof badge === "string") {
      return badge;
    }

    const base = badge ?? 0;

    if (children === undefined) {
      return base;
    }

    const value =
      base +
      (children.reduce((acc, child: Route.Item) => {
        const childBadgeValue = child.badge;
        if (typeof childBadgeValue === "number" && child.hidden !== true) {
          return acc + childBadgeValue;
        }
        return acc;
      }, 0) ?? 0);

    return value === 0 ? undefined : value;
  }, [badge, children]);
};

const useIsActive = (parent: string, route: RouteObject) => {
  const { path, children } = route;

  const { pathname } = useLocation();
  const root = useMemo(() => pathJoin(parent, path ?? ""), [parent, path]);

  const paths = useMemo(
    () => [root, ...(children?.map((v) => pathJoin(root, v.path ?? "")) ?? [])],
    [root, children],
  );

  const selection = useSelection().selection;
  return useMemo(
    () =>
      selection?.includes(root) ||
      paths.some((path) => matchPath(path, pathname)),
    [pathname, paths, root, selection],
  );
};

const themeCycle: {
  scheme: MantineColorScheme;
  icon: IconDefinition;
  label: string;
  color: string;
}[] = [
  { scheme: "auto", icon: faCircleHalfStroke, label: "Auto", color: "brand" },
  { scheme: "light", icon: faSun, label: "Light", color: "warning" },
  { scheme: "dark", icon: faMoon, label: "Dark", color: "info" },
];

const ThemeSwitcher: FunctionComponent = () => {
  const { setColorScheme } = useMantineColorScheme();

  const client = useQueryClient();
  const settings = useSystemSettings();
  const { mutate } = useSettingsMutation({ silent: true });

  const current = (settings.data?.general.theme ??
    "auto") as MantineColorScheme;

  const index = Math.max(
    0,
    themeCycle.findIndex((t) => t.scheme === current),
  );
  const active = themeCycle[index];

  const cycle = () => {
    const next = themeCycle[(index + 1) % themeCycle.length];

    // Apply immediately for instant feedback.
    setColorScheme(next.scheme);

    // Optimistically update the cached settings so everything reading them
    // (this button, ThemeLoader, Settings/UI) reflects the change instantly.
    const queryKey = [QueryKeys.System, QueryKeys.Settings];
    const previous = client.getQueryData<Settings>(queryKey);

    client.setQueryData<Settings>(queryKey, (old) =>
      old ? { ...old, general: { ...old.general, theme: next.scheme } } : old,
    );

    // Persist through the same settings system as Settings/UI, in the
    // background; roll back if the save fails.
    mutate(
      { "settings-general-theme": next.scheme },
      {
        onError: () => {
          client.setQueryData(queryKey, previous);
          setColorScheme(current);
        },
      },
    );
  };

  return (
    <Action
      label={`Theme: ${active.label}`}
      icon={active.icon}
      c={active.color}
      onClick={cycle}
    ></Action>
  );
};

const AppNavbar: FunctionComponent = () => {
  const [selection, select] = useState<string | null>(null);

  const routes = useRouteItems();

  const { pathname } = useLocation();
  useEffect(() => {
    select(null);
  }, [pathname]);

  return (
    <AppShell.Navbar p="xs" className={styles.nav}>
      <Selection.Provider value={{ selection, select }}>
        <AppShell.Section
          grow
          style={{ overflowY: "auto", scrollbarWidth: "none" }}
        >
          <Stack gap={0}>
            {routes.map((route, idx) => (
              <RouteItem
                key={BuildKey("nav", idx)}
                parent="/"
                route={route}
              ></RouteItem>
            ))}
          </Stack>
        </AppShell.Section>
        <Divider></Divider>
        <AppShell.Section mt="xs">
          <Group gap="xs">
            <ThemeSwitcher></ThemeSwitcher>
            <Anchor
              href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
              target="_blank"
            >
              <Action label="Donate" icon={faHeart} c="danger"></Action>
            </Anchor>
          </Group>
        </AppShell.Section>
      </Selection.Provider>
    </AppShell.Navbar>
  );
};

const RouteItem: FunctionComponent<{
  route: CustomRouteObject;
  parent: string;
}> = ({ route, parent }) => {
  const { children, name, path, icon, hidden, element } = route;

  const { select } = useSelection();

  const link = useMemo(() => pathJoin(parent, path ?? ""), [parent, path]);

  const badge = useBadgeValue(route);

  const isOpen = useIsActive(parent, route);

  // Ignore path if it is using match
  if (hidden === true || path === undefined || path.includes(":")) {
    return null;
  }

  if (children !== undefined) {
    const elements = (
      <Stack gap={0}>
        {children.map((child, idx) => (
          <RouteItem
            parent={link}
            key={BuildKey(link, "nav", idx)}
            route={child}
          ></RouteItem>
        ))}
      </Stack>
    );

    if (name) {
      return (
        <Stack gap={0}>
          <NavbarItem
            primary
            name={name}
            link={link}
            icon={icon}
            badge={badge}
            onClick={(event) => {
              LOG("info", "clicked", link);

              const validated =
                element !== undefined ||
                children?.find((v) => v.index === true) !== undefined;

              if (!validated) {
                event.preventDefault();
              }

              if (isOpen) {
                select(null);
              } else {
                select(link);
              }
            }}
          ></NavbarItem>
          <Collapse hidden={children.length === 0} expanded={isOpen}>
            {elements}
          </Collapse>
        </Stack>
      );
    } else {
      return elements;
    }
  } else {
    return (
      <NavbarItem
        name={name ?? link}
        link={link}
        icon={icon}
        badge={badge}
      ></NavbarItem>
    );
  }
};

interface NavbarItemProps {
  name: string;
  link: string;
  icon?: IconDefinition;
  badge?: number | string;
  primary?: boolean;
  onClick?: (event: React.MouseEvent<HTMLAnchorElement>) => void;
}

const NavbarItem: FunctionComponent<NavbarItemProps> = ({
  icon,
  link,
  name,
  badge,
  onClick,
  primary = false,
}) => {
  const { show } = useNavbar();

  const shouldHideBadge = useMemo(() => {
    if (typeof badge === "number") {
      return badge === 0;
    } else if (typeof badge === "string") {
      return badge.length === 0;
    }

    return true;
  }, [badge]);

  const isSignalRBadge = useMemo(() => {
    return link === "/series" || link === "/movies";
  }, [link]);

  // Compute explicit background and text style objects safely
  const badgeStyle = useMemo(() => {
    if (!isSignalRBadge) return {};

    if (badge === "LIVE") {
      return {
        // Subtle background colours that adapt to light/dark mode
        backgroundColor:
          "light-dark(var(--mantine-color-gray-0), var(--mantine-color-dark-6))",

        // Softened high-contrast text colors
        color:
          "light-dark(var(--mantine-color-gray-7), var(--mantine-color-gray-5))",

        border: "none",
      };
    }

    if (badge === "DOWN") {
      return {
        // more noticeable background colors for "DOWN" status, still adapting to theme
        backgroundColor:
          "light-dark(var(--mantine-color-danger-6), var(--mantine-color-danger-8))",
        color: "var(--mantine-color-white)",
      };
    }

    return {};
  }, [badge, isSignalRBadge]);

  return (
    <NavLink
      to={link}
      onClick={(event: React.MouseEvent<HTMLAnchorElement>) => {
        onClick?.(event);
        if (!event.isDefaultPrevented()) {
          show(false);
        }
      }}
      className={({ isActive }) =>
        clsx(styles.anchor, {
          [styles.active]: isActive,
        })
      }
    >
      <Text
        inline
        p="xs"
        size="sm"
        fw={primary ? "bold" : "normal"}
        className={styles.text}
        span
      >
        {icon && (
          <FontAwesomeIcon
            className={styles.icon}
            icon={icon}
          ></FontAwesomeIcon>
        )}
        {name}
        {!shouldHideBadge && (
          <Badge
            className={styles.badge}
            radius="xs"
            // We apply the explicit styling overrides here
            style={badgeStyle}
          >
            {badge}
          </Badge>
        )}
      </Text>
    </NavLink>
  );
};
export default AppNavbar;
