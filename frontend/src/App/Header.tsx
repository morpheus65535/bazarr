import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUser, faHeart } from "@fortawesome/free-solid-svg-icons";
import { Dropdown, Form, Nav, Navbar, NavLink, NavItem } from "react-bootstrap";

class Header extends React.Component {
  render() {
    return (
        <Navbar bg="light" expand="sm" className="header">
        <Nav className="mr-auto">
          <Form inline className="mr-4">
            <Form.Control
              type="text"
              size="sm"
              placeholder="Search..."
            ></Form.Control>
          </Form>
        </Nav>
        <Nav>
          <Nav.Link>
            <FontAwesomeIcon icon={faHeart}></FontAwesomeIcon>
          </Nav.Link>
          <Dropdown drop="left" as={NavItem}>
            <Dropdown.Toggle as={NavLink}>
              <FontAwesomeIcon icon={faUser}></FontAwesomeIcon>
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <Dropdown.Item>Restart</Dropdown.Item>
              <Dropdown.Item>Shutdown</Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
        </Nav>
      </Navbar>
    );
  }
}

export default Header;
