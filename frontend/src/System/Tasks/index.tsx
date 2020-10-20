import React from "react";
import { Container, Navbar, Nav, Button } from "react-bootstrap";
import { connect } from "react-redux";
import { UpdateSystemTasks } from "../../redux/actions/system";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSync } from "@fortawesome/free-solid-svg-icons";

import Table from "./table";

interface Props {
  update: () => void;
  loading: boolean;
}

function mapStateToProps({ system }: StoreState) {
  const { tasks } = system;
  return {
    loading: tasks.loading,
  };
}

class SystemStatus extends React.Component<Props, {}> {
  componentDidMount() {
    this.props.update();
  }

  render(): JSX.Element {
    const { loading } = this.props;
    return (
      <Container fluid className="p-0">
        <Navbar bg="dark">
          <Nav>
            <Button
              variant="dark"
              className="d-flex flex-column"
              disabled={loading}
              onClick={this.props.update}
            >
              <FontAwesomeIcon
                icon={faSync}
                spin={loading}
                size="lg"
                className="mx-auto"
              ></FontAwesomeIcon>
              <span className="align-bottom text-themecolor small text-center">
                Refresh
              </span>
            </Button>
          </Nav>
        </Navbar>
        <div className="p-3">
          <Table></Table>
        </div>
      </Container>
    );
  }
}

export default connect(mapStateToProps, { update: UpdateSystemTasks })(
  SystemStatus
);
