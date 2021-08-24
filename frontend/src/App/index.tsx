import "@fontsource/roboto/300.css";
import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Row } from "react-bootstrap";
import { Provider } from "react-redux";
import { Route, Switch } from "react-router";
import { BrowserRouter, Redirect } from "react-router-dom";
import { useEffectOnceWhen } from "rooks";
import Socketio from "../@modules/socketio";
import { useReduxStore } from "../@redux/hooks/base";
import { useNotification } from "../@redux/hooks/site";
import store from "../@redux/store";
import "../@scss/index.scss";
import { LoadingIndicator, ModalProvider } from "../components";
import Sidebar from "../Sidebar";
import Auth from "../special-pages/AuthPage";
import ErrorBoundary from "../special-pages/ErrorBoundary";
import LaunchError from "../special-pages/LaunchError";
import { useBaseUrl, useHasUpdateInject } from "../utilities";
import Header from "./Header";
import Router from "./Router";

// Sidebar Toggle
export const SidebarToggleContext = React.createContext<() => void>(() => {});

interface Props {}

const App: FunctionComponent<Props> = () => {
  const { initialized, auth } = useReduxStore((s) => s.site);

  const notify = useNotification("has-update", 10 * 1000);

  // Has any update?
  const hasUpdate = useHasUpdateInject();
  useEffectOnceWhen(() => {
    if (hasUpdate) {
      notify({
        type: "info",
        message: "A new version of Bazarr is ready, restart is required",
        // TODO: Restart action
      });
    }
  }, initialized === true);

  const [sidebar, setSidebar] = useState(false);
  const toggleSidebar = useCallback(() => setSidebar((s) => !s), []);

  if (!auth) {
    return <Redirect to="/login"></Redirect>;
  }

  if (typeof initialized === "boolean" && initialized === false) {
    return (
      <LoadingIndicator>
        <span>Please wait</span>
      </LoadingIndicator>
    );
  } else if (typeof initialized === "string") {
    return <LaunchError>{initialized}</LaunchError>;
  }
  return (
    <ErrorBoundary>
      <SidebarToggleContext.Provider value={toggleSidebar}>
        <Row noGutters className="header-container">
          <Header></Header>
        </Row>
        <Row noGutters className="flex-nowrap">
          <Sidebar open={sidebar}></Sidebar>
          <ModalProvider>
            <Router className="d-flex flex-row flex-grow-1 main-router"></Router>
          </ModalProvider>
        </Row>
      </SidebarToggleContext.Provider>
    </ErrorBoundary>
  );
};

const MainRouter: FunctionComponent = () => {
  const baseUrl = useBaseUrl();

  useEffect(() => {
    Socketio.initialize();
  }, []);

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

const Main: FunctionComponent = () => {
  return (
    <Provider store={store}>
      {/* TODO: Enabled Strict Mode after react-bootstrap upgrade to bootstrap 5 */}
      {/* <React.StrictMode> */}
      <MainRouter></MainRouter>
      {/* </React.StrictMode> */}
    </Provider>
  );
};

export default Main;
