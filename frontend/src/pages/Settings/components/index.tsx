import api from "apis/raw";
import { isBoolean, isNumber, isString } from "lodash";
import React, { FunctionComponent, useCallback, useState } from "react";
import { Button } from "react-bootstrap";
import { useLatest } from "./hooks";

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
    if (address && apikey && ssl !== null) {
      let testUrl: string;
      if (port) {
        testUrl = `${address}:${port}${url ?? ""}`;
      } else {
        testUrl = `${address}${url ?? ""}`;
      }
      const request = {
        protocol: ssl ? "https" : "http",
        url: testUrl,
        params: {
          apikey: apikey,
        },
      };

      if (!request.url.endsWith("/")) {
        request.url += "/";
      }

      api.utils
        .urlTest(request.protocol, request.url, request.params)
        .then((result) => {
          if (result.status) {
            setTitle(`Version: ${result.version}`);
            setVar("success");
          } else {
            setTitle(result.error);
            setVar("danger");
          }
        });
    }
  }, [address, port, url, apikey, ssl]);

  return (
    <Button
      onClick={click}
      variant={variant}
      title={title}
      className="text-truncate text-nowrap"
    >
      {title}
    </Button>
  );
};

export * from "./collapse";
export { default as CollapseBox } from "./collapse";
export * from "./container";
export * from "./forms";
export * from "./hooks";
export * from "./pathMapper";
export * from "./provider";
export { default as SettingsProvider } from "./provider";
