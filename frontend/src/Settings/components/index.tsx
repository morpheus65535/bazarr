import React, { FunctionComponent, useCallback, useState } from "react";
import { isString, isBoolean, isNumber } from "lodash";

import { Button } from "react-bootstrap";

import { useLatest } from "./hooks";

import { UtilsApi } from "../../apis";

export const URLTestButton: FunctionComponent<{
  category: "sonarr" | "radarr";
}> = ({ category }) => {
  const [title, setTitle] = useState("Test");
  const [variant, setVar] = useState("primary");

  const address = useLatest<string>(`settings-${category}-ip`, isString);
  const port = useLatest<number>(`settings-${category}-port`, isNumber);
  const url = useLatest<string>(`settings-${category}-base_url`, isString);
  const apikey = useLatest<string>(`settings-${category}-apikey`, isString);
  const ssl = useLatest<boolean>(`settings-${category}-ssl`, isBoolean);

  const click = useCallback(() => {
    if (address && port && apikey && ssl !== undefined) {
      const request = {
        protocol: ssl ? "https" : "http",
        url: `${address}:${port}${url ?? ""}`,
        params: {
          apikey: apikey,
        },
      };

      if (!request.url.endsWith("/")) {
        request.url += "/";
      }

      UtilsApi.urlTest(request.protocol, request.url, request.params).then(
        (result) => {
          if (result.status) {
            setTitle(`Version: ${result.version}`);
            setVar("success");
          } else {
            setTitle(result.error);
            setVar("danger");
          }
        }
      );
    }
  }, [address, port, url, apikey, ssl]);

  return (
    <Button
      onClick={click}
      variant={variant}
      title={title}
      className="text-overflow-ellipsis text-nowrap"
    >
      {title}
    </Button>
  );
};

export * from "./container";
export * from "./items";
export * from "./hooks";
export * from "./provider";
export * from "./collapse";
export { default as SettingsProvider } from "./provider";
export { default as CollapseBox } from "./collapse";
