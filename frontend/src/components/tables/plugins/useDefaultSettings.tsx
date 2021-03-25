import { Hooks, TableOptions } from "react-table";
import { useReduxStore } from "../../../@redux/hooks/base";

const pluginName = "useLocalSettings";

function useDefaultSettings<T extends object>(hooks: Hooks<T>) {
  hooks.useOptions.push(useOptions);
}
useDefaultSettings.pluginName = pluginName;

function useOptions<T extends object>(options: TableOptions<T>) {
  const { pageSize } = useReduxStore((s) => s.site);

  if (options.autoResetPage === undefined) {
    options.autoResetPage = false;
  }

  if (options.initialState === undefined) {
    options.initialState = {};
  }

  options.initialState.needLoadingScreen = false;

  if (options.initialState.pageSize === undefined) {
    options.initialState.pageSize = pageSize;
  }

  if (options.asyncLoader === undefined) {
    options.initialState.pageToLoad = undefined;
  }

  return options;
}

export default useDefaultSettings;
