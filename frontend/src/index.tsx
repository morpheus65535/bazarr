import "@fontsource/roboto/300.css";
import React from "react";
import ReactDOM from "react-dom";
import { QueryClientProvider } from "react-query";
import { Provider } from "react-redux";
import store from "./@redux/store";
import "./@scss/index.scss";
import queryClient from "./apis/queries";
import App from "./App";

ReactDOM.render(
  <Provider store={store}>
    <QueryClientProvider client={queryClient}>
      {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
      {/* <React.StrictMode> */}
      <App></App>
      {/* </React.StrictMode> */}
    </QueryClientProvider>
  </Provider>,
  document.getElementById("root")
);
