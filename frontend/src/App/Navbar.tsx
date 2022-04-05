import { setSidebar } from "@/modules/redux/actions";
import { useReduxAction } from "@/modules/redux/hooks/base";
import { useRouteItems } from "@/Router";
import { CustomRouteObject, Route } from "@/Router/type";
import { BuildKey, pathJoin } from "@/utilities";
import { LOG } from "@/utilities/console";
import { IconDefinition } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Badge,
  Button,
  Collapse,
  Navbar as MantineNavbar,
  Text,
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
  const [selection, select] = useState<string | null>(null);

  const routes = useRouteItems();

  const { pathname } = useLocation();
  useEffect(() => {
    select(null);
  }, [pathname]);

  return (
    <Selection.Provider value={{ selection, select }}>
      <MantineNavbar.Section>
        {routes.map((route, idx) => (
          <RouteItem
            key={BuildKey("nav", idx)}
            parent="/"
            route={route}
          ></RouteItem>
        ))}
      </MantineNavbar.Section>
    </Selection.Provider>
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

  const showSidebar = useReduxAction(setSidebar);

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
            fullWidth
            px="sm"
            variant={isOpen ? "filled" : "subtle"}
            leftIcon={icon && <FontAwesomeIcon icon={icon}></FontAwesomeIcon>}
            rightIcon={badge && <Badge hidden={badge === 0}>{badge}</Badge>}
            styles={{
              inner: { justifyContent: "flex-start" },
              icon: { width: "1.2rem", justifyContent: "center" },
            }}
            onClick={() => {
              LOG("info", "clicked", link);

              if (isValidated) {
                navigate(link);
                showSidebar(false);
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
          <Collapse in={isOpen}>
            <div>{elements}</div>
          </Collapse>
        </div>
      );
    } else {
      return <>{elements}</>;
    }
  } else {
    return (
      <NavLink to={link} onClick={() => showSidebar(false)}>
        <NavbarItem name={name ?? link} icon={icon} badge={badge}></NavbarItem>
      </NavLink>
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
