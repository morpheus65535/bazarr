import { IconDefinition } from "@fortawesome/free-solid-svg-icons";
import { RouteObject } from "react-router-dom";

declare namespace Route {
  export type Item = {
    icon?: IconDefinition;
    name?: string;
    badge?: number;
    hidden?: boolean;
    children?: Item[];
  };
}

export type CustomRouteObject = RouteObject & Route.Item;
