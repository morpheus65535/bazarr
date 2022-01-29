import { useResetProvider, useSystemProviders } from "@/apis/hooks";
import { ContentHeader, QueryOverlay } from "@/components";
import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import Table from "./table";

const SystemProvidersView: FunctionComponent = () => {
  const providers = useSystemProviders();

  const { isFetching, data, refetch } = providers;

  const { mutate: reset, isLoading: isResetting } = useResetProvider();

  return (
    <QueryOverlay result={providers}>
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
          <ContentHeader.Button
            icon={faTrash}
            updating={isResetting}
            onClick={() => reset()}
          >
            Reset
          </ContentHeader.Button>
        </ContentHeader>
        <Row>
          <Table providers={data ?? []}></Table>
        </Row>
      </Container>
    </QueryOverlay>
  );
};

export default SystemProvidersView;
