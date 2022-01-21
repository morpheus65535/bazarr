import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import api from "src/apis/raw";
import { useSystemProviders } from "../../apis/queries/client";
import { ContentHeader, QueryOverlay } from "../../components";
import Table from "./table";

interface Props {}

const SystemProvidersView: FunctionComponent<Props> = () => {
  const providers = useSystemProviders();

  return (
    <QueryOverlay {...providers}>
      {({ data, isFetching, refetch }) => (
        <Container fluid>
          <Helmet>
            <title>Providers - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={isFetching}
              icon={faSync}
              onClick={() => refetch()}
            >
              Refresh
            </ContentHeader.Button>
            <ContentHeader.AsyncButton
              icon={faTrash}
              promise={() => api.providers.reset()}
              onSuccess={() => refetch()}
            >
              Reset
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <Table providers={data ?? []}></Table>
          </Row>
        </Container>
      )}
    </QueryOverlay>
  );
};

export default SystemProvidersView;
