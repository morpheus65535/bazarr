import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { UpdateSystemLogs } from "../../@redux/actions";

import { faTrash, faDownload, faSync } from "@fortawesome/free-solid-svg-icons";
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
        <ContentHeader>
          <ContentHeaderButton
            updating={loading}
            icon={faSync}
            disabled={loading}
            onClick={update}
          >
            Refresh
          </ContentHeaderButton>
          <ContentHeaderButton icon={faDownload}>Download</ContentHeaderButton>
          <ContentHeaderButton
            updating={resetting}
            icon={faTrash}
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
