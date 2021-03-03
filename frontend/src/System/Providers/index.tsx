import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { providerUpdateAll } from "../../@redux/actions";
import { ProvidersApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import { useProviders } from "../../utilites/items";
import Table from "./table";

interface Props {
  update: () => void;
}

const SystemProvidersView: FunctionComponent<Props> = ({ update }) => {
  const providers = useProviders();

  return (
    <AsyncStateOverlay state={providers}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Providers - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={providers.updating}
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
            <Table providers={data}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(undefined, { update: providerUpdateAll })(
  SystemProvidersView
);
