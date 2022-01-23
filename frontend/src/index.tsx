import queryClient from "@/apis/queries";
import store from "@/modules/redux/store";
import "@/styles/index.scss";
import "@fontsource/roboto/300.css";
import React from "react";
import ReactDOM from "react-dom";
import { QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import { Provider } from "react-redux";
import { useRoutes } from "react-router-dom";
import { Router, useRouteItems } from "./Router";
import { Environment } from "./utilities";

const RouteApp = () => {
  const items = useRouteItems();

  return useRoutes(items);
};

export const Entrance = () => (
  <Provider store={store}>
    <QueryClientProvider client={queryClient}>
      <Router>
        {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
        {/* <React.StrictMode> */}
        {Environment.queryDev && <ReactQueryDevtools initialIsOpen={false} />}
        <RouteApp></RouteApp>
        {/* </React.StrictMode> */}
      </Router>
    </QueryClientProvider>
  </Provider>
);

ReactDOM.render(<Entrance />, document.getElementById("root"));
