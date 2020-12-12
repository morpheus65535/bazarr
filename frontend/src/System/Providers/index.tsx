import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { UpdateSystemProviders } from "../../@redux/actions/system";

import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import { ContentHeader, ContentHeaderButton } from "../../components";

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
        <Row>
          <ContentHeader>
            <ContentHeaderButton
              iconProps={{ icon: faSync, spin: loading }}
              disabled={loading}
              onClick={this.props.update}
            >
              Refresh
            </ContentHeaderButton>
            <ContentHeaderButton iconProps={{ icon: faTrash }}>
              Reset
            </ContentHeaderButton>
          </ContentHeader>
        </Row>
        <Row className="p-3">
          <Table></Table>
        </Row>
      </Container>
    );
  }
}

export default connect(mapStateToProps, { update: UpdateSystemProviders })(
  SystemProvidersView
);
