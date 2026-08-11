import { FunctionComponent, useMemo } from "react";
import { useNavigate } from "react-router";
import { Image, rem } from "@mantine/core";
import {
  Spotlight,
  SpotlightActionData,
  SpotlightActionGroupData,
  useSpotlight,
} from "@mantine/spotlight";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useServerSearch } from "@/apis/hooks";
import { CustomRouteObject } from "@/Router/type";
import { useRouteItems } from "@/Router/useRouteItems";
import { useDebouncedValue } from "@/utilities";
import { spotlightStore } from "./spotlight";

const buildNavActions = (
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
      if (route.hidden) continue;

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

const AppSpotlight: FunctionComponent = () => {
  const navigate = useNavigate();
  const routes = useRouteItems();
  const { query } = useSpotlight(spotlightStore);
  const debouncedQuery = useDebouncedValue(query, 300);
  const { data: searchResults } = useServerSearch(
    debouncedQuery,
    debouncedQuery.length >= 2,
  );

  const navActions = useMemo(
    () => buildNavActions(routes, navigate),
    [routes, navigate],
  );

  const searchActions = useMemo<SpotlightActionData[]>(() => {
    if (!searchResults?.length) return [];

    return searchResults.reduce<SpotlightActionData[]>((acc, v) => {
      if (v.sonarrSeriesId != null) {
        const link = `/series/${v.sonarrSeriesId}`;
        acc.push({
          id: link,
          label: `${v.title} (${v.year})`,
          description: "Series",
          leftSection: <Image src={v.poster} w={55} h={78} fit="cover" />,
          onClick: () => navigate(link),
        });
        return acc;
      }

      if (v.radarrId != null) {
        const link = `/movies/${v.radarrId}`;
        acc.push({
          id: link,
          label: `${v.title} (${v.year})`,
          description: "Movie",
          leftSection: <Image src={v.poster} w={55} h={78} fit="cover" />,
          onClick: () => navigate(link),
        });
        return acc;
      }

      return acc;
    }, []);
  }, [searchResults, navigate]);

  const actions = useMemo<
    (SpotlightActionData | SpotlightActionGroupData)[]
  >(() => {
    const result: (SpotlightActionData | SpotlightActionGroupData)[] = [];

    if (navActions.length > 0) {
      result.push({ group: "Navigation", actions: navActions });
    }

    if (searchActions.length > 0) {
      result.push({ group: "Series & Movies", actions: searchActions });
    }

    return result;
  }, [navActions, searchActions]);

  return (
    <Spotlight
      store={spotlightStore}
      actions={actions}
      nothingFound="No results found"
      scrollable
      // Uniform row height so actions without a description (e.g. Series,
      // Movies) match the taller two-line ones; content stays centered and
      // long labels can still grow past it.
      styles={{ action: { minHeight: rem(52) } }}
    />
  );
};

export default AppSpotlight;
