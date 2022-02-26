import { Hooks, TableOptions } from "react-table";
import { usePageSize } from "utilities/storage";

const pluginName = "useLocalSettings";

function useDefaultSettings<T extends object>(hooks: Hooks<T>) {
  hooks.useOptions.push(useOptions);
}
useDefaultSettings.pluginName = pluginName;

function useOptions<T extends object>(options: TableOptions<T>) {
  const [pageSize] = usePageSize();

  if (options.autoResetPage === undefined) {
    options.autoResetPage = false;
  }

  if (options.autoResetExpanded === undefined) {
    options.autoResetExpanded = false;
  }

  if (options.initialState === undefined) {
    options.initialState = {};
  }

  if (options.initialState.pageSize === undefined) {
    options.initialState.pageSize = pageSize;
  }

  return options;
}

export default useDefaultSettings;
