import api from "@/apis/raw";
import { Button } from "@mantine/core";
import { FunctionComponent, useCallback, useState } from "react";
import { useSettingValue } from "../utilities/hooks";

export const URLTestButton: FunctionComponent<{
  category: "sonarr" | "radarr";
}> = ({ category }) => {
  const [title, setTitle] = useState("Test");
  const [color, setVar] = useState("primary");

  const address = useSettingValue<string>(`settings-${category}-ip`);
  const port = useSettingValue<number>(`settings-${category}-port`);
  const url = useSettingValue<string>(`settings-${category}-base_url`);
  const apikey = useSettingValue<string>(`settings-${category}-apikey`);
  const ssl = useSettingValue<boolean>(`settings-${category}-ssl`);

  const click = useCallback(() => {
    if (address && apikey && ssl !== null) {
      let testUrl: string;

      let baseUrl = url;
      if (baseUrl && baseUrl.startsWith("/") === false) {
        baseUrl = "/" + baseUrl;
      }

      if (port) {
        testUrl = `${address}:${port}${baseUrl ?? ""}`;
      } else {
        testUrl = `${address}${baseUrl ?? ""}`;
      }
      const request = {
        protocol: ssl ? "https" : "http",
        url: testUrl,
        params: {
          apikey,
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
    <Button onClick={click} color={color} title={title}>
      {title}
    </Button>
  );
};

export * from "./Card";
export * from "./Layout";
export { default as Layout } from "./Layout";
export { default as LayoutModal } from "./LayoutModal";
export * from "./Message";
export * from "./Section";
export * from "./collapse";
export { default as CollapseBox } from "./collapse";
export * from "./forms";
export * from "./pathMapper";
