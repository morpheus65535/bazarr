import { useReduxStore } from "@redux/hooks/base";
import logo from "@static/logo128.png";
import { useSystem } from "apis/hooks";
import React, { FunctionComponent, useState } from "react";
import { Button, Card, Form, Image, Spinner } from "react-bootstrap";
import { Redirect } from "react-router-dom";
import "./Authentication.scss";

interface Props {}

const Authentication: FunctionComponent<Props> = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const { login, isWorking } = useSystem();

  const authState = useReduxStore((s) => s.auth);

  if (authState) {
    return <Redirect to="/"></Redirect>;
  }

  return (
    <div className="d-flex bg-light vh-100 justify-content-center align-items-center">
      <Card className="auth-card shadow">
        <Form
          onSubmit={(e) => {
            e.preventDefault();
            login({ username, password });
          }}
        >
          <Card.Body>
            <Form.Group className="mb-5 d-flex justify-content-center">
              <Image width="64" height="64" src={logo}></Image>
            </Form.Group>
            <Form.Group>
              <Form.Control
                disabled={isWorking}
                name="username"
                type="text"
                placeholder="Username"
                required
                onChange={(e) => setUsername(e.currentTarget.value)}
              ></Form.Control>
            </Form.Group>
            <Form.Group>
              <Form.Control
                disabled={isWorking}
                name="password"
                type="password"
                placeholder="Password"
                required
                onChange={(e) => setPassword(e.currentTarget.value)}
              ></Form.Control>
            </Form.Group>
            {/* <Collapse in={error.length !== 0}>
              <div>
                <Alert variant="danger" className="m-0">
                  {error}
                </Alert>
              </div>
            </Collapse> */}
          </Card.Body>
          <Card.Footer>
            <Button type="submit" disabled={isWorking} block>
              {isWorking ? (
                <Spinner size="sm" animation="border"></Spinner>
              ) : (
                "LOGIN"
              )}
            </Button>
          </Card.Footer>
        </Form>
      </Card>
    </div>
  );
};

export default Authentication;
