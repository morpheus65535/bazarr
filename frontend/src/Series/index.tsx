import React from "react";
import { connect } from "react-redux";
import { Button, Container, Nav, Navbar } from "react-bootstrap";

import { faList } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { updateSeriesList } from "../redux/actions/common";

import Table from "./table";

interface Props {
  updateSeriesList: () => void;
}

class Series extends React.Component<Props, {}> {
  componentDidMount() {
    this.props.updateSeriesList()
  }
  render(): JSX.Element {
    return (
      <Container fluid className="px-0">
        <Navbar bg="dark">
          <Nav>
            <Button variant="dark" className="d-flex flex-column">
              <FontAwesomeIcon
                icon={faList}
                size="lg"
                className="mx-auto"
              ></FontAwesomeIcon>
              <span className="align-bottom text-themecolor small text-center">
                Mass Edit
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

export default connect(null, { updateSeriesList })(Series);
