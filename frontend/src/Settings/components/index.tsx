import React, { FunctionComponent, useState } from "react";

import { Button } from "react-bootstrap";

import { UtilsApi } from "../../apis";

type TestResponse =
  | {
      status: true;
      version: string;
    }
  | {
      status: false;
      error: string;
    };

export interface TestUrl {
  address: string;
  port: string;
  url: string;
  apikey: string;
  ssl: boolean;
}

interface TestUrlButtonProps {
  url: TestUrl;
}

export const TestUrlButton: FunctionComponent<TestUrlButtonProps> = ({
  url,
}) => {
  function buildRequest(
    props: TestUrl
  ): { protocol: string; url: string; params: LooseObject } {
    const request = {
      protocol: props.ssl ? "https" : "http",
      url: `${props.address}:${props.port}${props.url}`,
      params: {
        apikey: props.apikey,
      },
    };

    if (!request.url.endsWith("/")) {
      request.url += "/";
    }

    return request;
  }

  const [title, setTitle] = useState("Test");
  const [variant, setVar] = useState("primary");

  const click = () => {
    const request = buildRequest(url);

    UtilsApi.urlTest<TestResponse>(
      request.protocol,
      request.url,
      request.params
    ).then((result) => {
      if (result.status) {
        setTitle(`Version: ${result.version}`);
        setVar("success");
      } else {
        setTitle(result.error);
        setVar("danger");
      }
    });
  };

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
