import { useNavigate } from "react-router";
import { SpotlightActionData } from "@mantine/spotlight";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { CustomRouteObject } from "@/Router/type";

export const buildNavActions = (
  routes: CustomRouteObject[],
  navigate: ReturnType<typeof useNavigate>,
): SpotlightActionData[] => {
  const actions: SpotlightActionData[] = [];

  const walk = (
    routeList: CustomRouteObject[],
    parentPath: string,
    parentName?: string,
    parentIcon?: IconDefinition,
  ): void => {
    for (const route of routeList) {
      // Hidden routes are excluded from the sidebar, but named children of
      // settings groups (the tab pages) should still be searchable. Unnamed
      // hidden routes (legacy redirects) stay excluded.
      if (route.hidden && !(route.name && parentPath.startsWith("/settings"))) {
        continue;
      }

      const fullPath = (
        route.path?.startsWith("/")
          ? route.path
          : route.path
            ? parentPath
              ? `${parentPath}/${route.path}`
              : `/${route.path}`
            : parentPath
      ).replace(/\/+/g, "/");

      if (fullPath.includes(":")) continue;

      if (
        route.name &&
        (route.element || route.children?.some((c) => c.index))
      ) {
        const icon = route.icon || parentIcon;
        actions.push({
          id: fullPath,
          label: route.name,
          description: parentName,
          leftSection: icon ? <FontAwesomeIcon icon={icon} /> : undefined,
          onClick: () => navigate(fullPath),
        });
      }

      if (route.children) {
        walk(
          route.children,
          fullPath,
          route.name || parentName,
          route.icon || parentIcon,
        );
      }
    }
  };

  walk(routes, "");
  return actions;
};
