import React from "react";
import ReactDOM from "react-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import App from "./App";

import "./@scss/index.scss";

import { Provider } from "react-redux";
import store from "./@redux/store";

ReactDOM.render(
  <Provider store={store}>
    {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
    {/* <React.StrictMode> */}
    <App />
    {/* </React.StrictMode> */}
  </Provider>,
  document.getElementById("root")
);
