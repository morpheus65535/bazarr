import { FunctionComponent, useCallback, useEffect, useState } from "react";
import { Button } from "@mantine/core";
import api from "@/apis/raw";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";

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
    <Button autoContrast onClick={click} variant={color} title={title}>
      {title}
    </Button>
  );
};

export const ProviderTestButton: FunctionComponent<{
  category: string;
}> = ({ category }) => {
  const testConnection = "Test Connection";
  const [title, setTitle] = useState(testConnection);
  const [color, setVar] = useState("primary");

  const testUrl = useSettingValue<string>(`settings-${category}-endpoint`);

  const click = useCallback(() => {
    if (testUrl !== null) {
      const urlWithoutProtocol = new URL(testUrl).host;
      const request = {
        protocol: "http",
        url: urlWithoutProtocol,
      };
      if (!request.url.endsWith("/")) {
        request.url += "/";
      }

      api.utils
        .providerUrlTest(request.protocol, request.url)
        .then((result) => {
          if (result.status) {
            setTitle(`${result.version}`);
            setVar("success");
          } else {
            setVar("danger");
            if (result.code === 404) {
              setTitle(
                "Connected but no version found (possibly whisper-asr?)",
              );
            } else {
              setTitle(result.error);
            }
          }
        });
    }
  }, [testUrl]);

  useEffect(() => {
    setTitle(testConnection);
  }, [testUrl]);

  return (
    <Button onClick={click} variant={color} title={title}>
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
