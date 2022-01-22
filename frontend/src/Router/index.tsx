import { FunctionComponent } from "react";
import { Redirect, Route, Switch, useHistory } from "react-router";
import { useDidMount } from "rooks";
import { BuildKey, ScrollToTop } from "utilities";
import { useNavigationItems } from "../Navigation";
import { Navigation } from "../Navigation/nav";
import { RouterEmptyPath } from "../special-pages/404";

const Router: FunctionComponent = () => {
  const navItems = useNavigationItems();

  const history = useHistory();
  useDidMount(() => {
    history.listen(() => {
      // This is a hack to make sure ScrollToTop will be triggered in the next frame (When everything are loaded)
      setTimeout(ScrollToTop);
    });
  });

  return (
    <div className="d-flex flex-row flex-grow-1 main-router">
      <Switch>
        {navItems.map((v, idx) => {
          if ("routes" in v) {
            return (
              <Route path={v.path} key={BuildKey(idx, v.name, "router")}>
                <ParentRouter {...v}></ParentRouter>
              </Route>
            );
          } else if (v.enabled !== false) {
            return (
              <Route
                key={BuildKey(idx, v.name, "root")}
                exact
                path={v.path}
                component={v.component}
              ></Route>
            );
          } else {
            return null;
          }
        })}
        <Route path="*">
          <Redirect to={RouterEmptyPath}></Redirect>
        </Route>
      </Switch>
    </div>
  );
};

export default Router;

const ParentRouter: FunctionComponent<Navigation.RouteWithChild> = ({
  path,
  enabled,
  component,
  routes,
}) => {
  if (enabled === false || (component === undefined && routes.length === 0)) {
    return null;
  }
  const ParentComponent =
    component ?? (() => <Redirect to={path + routes[0].path}></Redirect>);

  return (
    <Switch>
      <Route exact path={path} component={ParentComponent}></Route>
      {routes
        .filter((v) => v.enabled !== false)
        .map((v, idx) => (
          <Route
            key={BuildKey(idx, v.name, "route")}
            exact
            path={path + v.path}
            component={v.component}
          ></Route>
        ))}
      <Route path="*">
        <Redirect to={RouterEmptyPath}></Redirect>
      </Route>
    </Switch>
  );
};
