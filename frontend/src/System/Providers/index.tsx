import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { UpdateProviderList } from "../../@redux/actions";

import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import { ContentHeader, ContentHeaderButton } from "../../Components";

import Table from "./table";

interface Props {
  loading: boolean;
  update: () => void;
}

function mapStateToProps({ system }: StoreState) {
  const { providers } = system;
  return {
    loading: providers.updating,
  };
}

class SystemProvidersView extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render(): JSX.Element {
    const { loading, update } = this.props;
    return (
      <Container fluid>
        <Helmet>
          <title>Providers - Bazarr (System)</title>
        </Helmet>
        <ContentHeader>
          <ContentHeaderButton
            updating={loading}
            icon={faSync}
            disabled={loading}
            onClick={update}
          >
            Refresh
          </ContentHeaderButton>
          <ContentHeaderButton icon={faTrash}>Reset</ContentHeaderButton>
        </ContentHeader>
        <Row>
          <Table></Table>
        </Row>
      </Container>
    );
  }
}

export default connect(mapStateToProps, { update: UpdateProviderList })(
  SystemProvidersView
);
