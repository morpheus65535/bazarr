import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { UpdateSystemLogs } from "../../@redux/actions";

import {
  faSync,
  faTrash,
  faDownload,
  faSpinner,
} from "@fortawesome/free-solid-svg-icons";
import { ContentHeader, ContentHeaderButton } from "../../Components";

import Table from "./table";

import { SystemApi } from "../../apis";

interface Props {
  loading: boolean;
  update: () => void;
}

interface State {
  resetting: boolean;
}

function mapStateToProps({ system }: StoreState) {
  const { logs } = system;
  return {
    loading: logs.updating,
  };
}

class SystemLogsView extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      resetting: false,
    };
  }
  componentDidMount() {
    this.props.update();
  }
  render(): JSX.Element {
    const { loading, update } = this.props;
    const { resetting } = this.state;
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
              onClick={update}
            >
              Refresh
            </ContentHeaderButton>
            <ContentHeaderButton iconProps={{ icon: faDownload }}>
              Download
            </ContentHeaderButton>
            <ContentHeaderButton
              disabled={resetting}
              iconProps={{
                icon: resetting ? faSpinner : faTrash,
                spin: resetting,
              }}
              onClick={() => {
                this.setState({ ...this.state, resetting: true });
                SystemApi.deleteLogs().finally(() => {
                  this.setState({ ...this.state, resetting: false });
                  update();
                });
              }}
            >
              Empty
            </ContentHeaderButton>
          </ContentHeader>
        </Row>
        <Row>
          <Table></Table>
        </Row>
      </Container>
    );
  }
}

export default connect(mapStateToProps, { update: UpdateSystemLogs })(
  SystemLogsView
);
