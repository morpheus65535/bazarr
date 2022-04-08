import { Action } from "@/components";
import { Layout } from "@/constants";
import { useNavbar } from "@/contexts/Navbar";
import { useRouteItems } from "@/Router";
import { CustomRouteObject, Route } from "@/Router/type";
import { BuildKey, pathJoin } from "@/utilities";
import { LOG } from "@/utilities/console";
import {
  faHeart,
  faMoon,
  faSun,
  IconDefinition,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Anchor,
  Badge,
  Button,
  Collapse,
  Divider,
  Group,
  Navbar as MantineNavbar,
  Stack,
  Text,
  useMantineColorScheme,
} from "@mantine/core";
import {
  createContext,
  FunctionComponent,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  matchPath,
  NavLink,
  RouteObject,
  useLocation,
  useNavigate,
} from "react-router-dom";

const Selection = createContext<{
  selection: string | null;
  select: (path: string | null) => void;
}>({
  selection: null,
  select: () => {
    LOG("error", "Selection context not initialized");
  },
});

function useSelection() {
  return useContext(Selection);
}

function useBadgeValue(route: Route.Item) {
  const { badge, children } = route;
  return useMemo(() => {
    let value = badge ?? 0;

    if (children === undefined) {
      return value;
    }

    value +=
      children.reduce((acc, child: Route.Item) => {
        if (child.badge && child.hidden !== true) {
          return acc + (child.badge ?? 0);
        }
        return acc;
      }, 0) ?? 0;

    return value === 0 ? undefined : value;
  }, [badge, children]);
}

function useIsActive(parent: string, route: RouteObject) {
  const { path, children } = route;

  const { pathname } = useLocation();
  const root = useMemo(() => pathJoin(parent, path ?? ""), [parent, path]);

  const paths = useMemo(
    () => [root, ...(children?.map((v) => pathJoin(root, v.path ?? "")) ?? [])],
    [root, children]
  );

  const selection = useSelection().selection;
  return useMemo(
    () =>
      selection?.includes(root) ||
      paths.some((path) => matchPath(path, pathname)),
    [pathname, paths, root, selection]
  );
}

const AppNavbar: FunctionComponent = () => {
  const { showed } = useNavbar();
  const [selection, select] = useState<string | null>(null);

  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const dark = colorScheme === "dark";

  const routes = useRouteItems();

  const { pathname } = useLocation();
  useEffect(() => {
    select(null);
  }, [pathname]);

  return (
    <MantineNavbar
      p="xs"
      hiddenBreakpoint={Layout.MOBILE_BREAKPOINT}
      hidden={!showed}
      width={{ [Layout.MOBILE_BREAKPOINT]: Layout.NAVBAR_WIDTH }}
      styles={(theme) => ({
        root: {
          backgroundColor:
            theme.colorScheme === "light"
              ? theme.colors.gray[2]
              : theme.colors.dark[6],
        },
      })}
    >
      <Selection.Provider value={{ selection, select }}>
        <MantineNavbar.Section grow>
          <Stack spacing="xs">
            {routes.map((route, idx) => (
              <RouteItem
                key={BuildKey("nav", idx)}
                parent="/"
                route={route}
              ></RouteItem>
            ))}
          </Stack>
        </MantineNavbar.Section>
        <Divider></Divider>
        <MantineNavbar.Section mt="xs">
          <Group spacing="xs">
            <Action
              color={dark ? "yellow" : "indigo"}
              variant="hover"
              onClick={() => toggleColorScheme()}
              icon={dark ? faSun : faMoon}
            ></Action>
            <Anchor
              href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
              target="_blank"
            >
              <Action icon={faHeart} variant="hover" color="red"></Action>
            </Anchor>
          </Group>
        </MantineNavbar.Section>
      </Selection.Provider>
    </MantineNavbar>
  );
};

const RouteItem: FunctionComponent<{
  route: CustomRouteObject;
  parent: string;
}> = ({ route, parent }) => {
  const { children, name, path, icon, hidden, element } = route;

  const isValidated = useMemo(
    () =>
      element !== undefined ||
      children?.find((v) => v.index === true) !== undefined,
    [element, children]
  );

  const { show } = useNavbar();

  const { select } = useSelection();

  const navigate = useNavigate();

  const link = useMemo(() => pathJoin(parent, path ?? ""), [parent, path]);

  const badge = useBadgeValue(route);

  const isOpen = useIsActive(parent, route);

  if (hidden === true) {
    return null;
  }

  // Ignore path if it is using match
  if (path === undefined || path.includes(":")) {
    return null;
  }

  if (children !== undefined) {
    const elements = children.map((child, idx) => (
      <RouteItem
        parent={link}
        key={BuildKey(link, "nav", idx)}
        route={child}
      ></RouteItem>
    ));

    if (name) {
      return (
        <div>
          <Button
            color="dark"
            fullWidth
            px="sm"
            variant={isOpen ? "filled" : "subtle"}
            leftIcon={icon && <FontAwesomeIcon icon={icon} />}
            rightIcon={badge && <Badge hidden={badge === 0}>{badge}</Badge>}
            styles={{
              inner: { justifyContent: "flex-start" },
              icon: { width: "1.2rem", justifyContent: "center" },
              rightIcon: { justifySelf: "flex-end" },
            }}
            onClick={() => {
              LOG("info", "clicked", link);

              if (isValidated) {
                navigate(link);
                show(false);
              }

              if (isOpen) {
                select(null);
              } else {
                select(link);
              }
            }}
          >
            <NavbarItem name={name ?? link}></NavbarItem>
          </Button>
          <Collapse hidden={children.length === 0} in={isOpen}>
            <div>{elements}</div>
          </Collapse>
        </div>
      );
    } else {
      return <>{elements}</>;
    }
  } else {
    return (
      <Anchor component={NavLink} to={link} onClick={() => show(false)}>
        <NavbarItem name={name ?? link} icon={icon} badge={badge}></NavbarItem>
      </Anchor>
    );
  }
};

interface NavbarItemProps {
  name: string;
  icon?: IconDefinition;
  badge?: number;
}

const NavbarItem: FunctionComponent<NavbarItemProps> = ({
  icon,
  name,
  badge,
}) => {
  return <Text>{name}</Text>;
};

export default AppNavbar;
