import queryClient from "@/apis/queries";
import store from "@/modules/redux/store";
import "@/styles/index.scss";
import "@fontsource/roboto/300.css";
import React from "react";
import ReactDOM from "react-dom";
import { QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";
import { Provider } from "react-redux";
import App from "./App";
import { Environment } from "./utilities";

export const Entrance = () => (
  <Provider store={store}>
    <QueryClientProvider client={queryClient}>
      {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
      {/* <React.StrictMode> */}
      {Environment.queryDev && <ReactQueryDevtools initialIsOpen={false} />}
      <App></App>
      {/* </React.StrictMode> */}
    </QueryClientProvider>
  </Provider>
);

ReactDOM.render(<Entrance />, document.getElementById("root"));
