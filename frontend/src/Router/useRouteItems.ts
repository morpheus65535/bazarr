import { createContext, useContext } from "react";
import { CustomRouteObject } from "@/Router/type";

export const RouterItemContext = createContext<CustomRouteObject[]>([]);

export const useRouteItems = () => useContext(RouterItemContext);
