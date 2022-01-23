import queryClient from "@/apis/queries";
import store from "@/modules/redux/store";
import "@/styles/index.scss";
import "@fontsource/roboto/300.css";
import React, { FunctionComponent } from "react";
import ReactDOM from "react-dom";
import { QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import { Provider } from "react-redux";
import { BrowserRouter as Router, useRoutes } from "react-router-dom";
import { routes } from "./Router";
import { Environment } from "./utilities";

const RouteApp: FunctionComponent = () => useRoutes(routes);

export const Entrance = () => (
  <Provider store={store}>
    <Router>
      <QueryClientProvider client={queryClient}>
        {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
        {/* <React.StrictMode> */}
        {Environment.queryDev && <ReactQueryDevtools initialIsOpen={false} />}
        <RouteApp></RouteApp>
        {/* </React.StrictMode> */}
      </QueryClientProvider>
    </Router>
  </Provider>
);

ReactDOM.render(<Entrance />, document.getElementById("root"));
