import "fontsource-roboto";
import React, { FunctionComponent } from "react";
import ReactDOM from "react-dom";
import { Provider } from "react-redux";
import { Route, Switch } from "react-router";
import { BrowserRouter } from "react-router-dom";
import store from "./@redux/store";
import "./@scss/index.scss";
import App from "./App";
import Auth from "./Auth";
import { useBaseUrl } from "./utilites";

const MainRouter: FunctionComponent = () => {
  const baseUrl = useBaseUrl();

  return (
    <BrowserRouter basename={baseUrl}>
      <Switch>
        <Route exact path="/login">
          <Auth></Auth>
        </Route>
        <Route path="/">
          <App></App>
        </Route>
      </Switch>
    </BrowserRouter>
  );
};

ReactDOM.render(
  <Provider store={store}>
    {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
    {/* <React.StrictMode> */}
    <MainRouter></MainRouter>
    {/* </React.StrictMode> */}
  </Provider>,
  document.getElementById("root")
);
