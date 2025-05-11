import { RouteObject } from "react-router";
import { IconDefinition } from "@fortawesome/free-solid-svg-icons";

declare namespace Route {
  export type Item = {
    icon?: IconDefinition;
    name?: string;
    badge?: number | string;
    hidden?: boolean;
    children?: Item[];
  };
}

export type CustomRouteObject = RouteObject & Route.Item;
