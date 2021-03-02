import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { providerUpdateAll } from "../../@redux/actions";
import { ProvidersApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  providers: AsyncState<SystemProvider[]>;
  update: () => void;
}

function mapStateToProps({ system }: ReduxStore) {
  const { providers } = system;
  return {
    providers,
  };
}

const SystemProvidersView: FunctionComponent<Props> = ({
  providers,
  update,
}) => {
  useEffect(() => {
    update();
  }, [update]);

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

export default connect(mapStateToProps, { update: providerUpdateAll })(
  SystemProvidersView
);
