import { useResetProvider, useSystemProviders } from "@/apis/hooks";
import { ContentHeader } from "@/components";
import { QueryOverlay } from "@/components/async";
import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import { Container } from "@mantine/core";
import { FunctionComponent } from "react";
import { Helmet } from "react-helmet";
import Table from "./table";

const SystemProvidersView: FunctionComponent = () => {
  const providers = useSystemProviders();

  const { isFetching, data, refetch } = providers;

  const { mutate: reset, isLoading: isResetting } = useResetProvider();

  return (
    <QueryOverlay result={providers}>
      <Container fluid px={0}>
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
        <Table providers={data ?? []}></Table>
      </Container>
    </QueryOverlay>
  );
};

export default SystemProvidersView;
