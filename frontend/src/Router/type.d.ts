import { RouteObject } from "react-router-dom";

export type Route = RouteObject & {
  name?: string;
  children?: Route[];
};
