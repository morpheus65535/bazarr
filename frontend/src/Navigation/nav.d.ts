import { IconDefinition } from "@fortawesome/free-solid-svg-icons";
import { FunctionComponent } from "react";

export declare namespace Navigation {
  type RouteWithoutChild = {
    icon?: IconDefinition;
    name: string;
    path: string;
    component: FunctionComponent;
    badge?: number;
    enabled?: boolean;
    routeOnly?: boolean;
  };

  type RouteWithChild = {
    icon: IconDefinition;
    name: string;
    path: string;
    component?: FunctionComponent;
    badge?: number;
    enabled?: boolean;
    routes: RouteWithoutChild[];
  };

  type RouteItem = RouteWithChild | RouteWithoutChild;
}
