import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSystemProviders } from "../../@redux/hooks";
import { ProvidersApi } from "../../apis";
import { AsyncOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {}

const SystemProvidersView: FunctionComponent<Props> = () => {
  const [providers, update] = useSystemProviders();

  return (
    <AsyncOverlay ctx={providers}>
      {({ content, state }) => (
        <Container fluid>
          <Helmet>
            <title>Providers - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={state === "loading"}
              icon={faSync}
              onClick={update}
            >
              Refresh
            </ContentHeader.Button>
            <ContentHeader.AsyncButton
              icon={faTrash}
              promise={() => ProvidersApi.reset()}
              onSuccess={update}
            >
              Reset
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <Table providers={content ?? []}></Table>
          </Row>
        </Container>
      )}
    </AsyncOverlay>
  );
};

export default SystemProvidersView;
