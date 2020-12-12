import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { UpdateSystemTasks } from "../../@redux/actions";
import { Helmet } from "react-helmet";

import { ContentHeader, ContentHeaderButton } from "../../Components";

import { faSync } from "@fortawesome/free-solid-svg-icons";

import Table from "./table";

interface Props {
  update: () => void;
  loading: boolean;
}

function mapStateToProps({ system }: StoreState) {
  const { tasks } = system;
  return {
    loading: tasks.updating,
  };
}

class SystemTasksView extends React.Component<Props, {}> {
  componentDidMount() {
    this.props.update();
  }

  render(): JSX.Element {
    const { loading, update } = this.props;
    return (
      <Container fluid>
        <Helmet>
          <title>Tasks - Bazarr (System)</title>
        </Helmet>
        <Row>
          <ContentHeader>
            <ContentHeaderButton
              iconProps={{ icon: faSync, spin: loading }}
              btnProps={{ disabled: loading }}
              onClick={update}
            >
              Refresh
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

export default connect(mapStateToProps, { update: UpdateSystemTasks })(
  SystemTasksView
);
