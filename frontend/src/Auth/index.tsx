import React, { FunctionComponent, useCallback, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Collapse,
  Form,
  Image,
  Spinner,
} from "react-bootstrap";
import { Redirect } from "react-router-dom";
import { siteAuthSuccess } from "../@redux/actions";
import { useReduxActionFunction, useReduxStore } from "../@redux/hooks/base";
import logo from "../@static/logo128.png";
import { SystemApi } from "../apis";
import "./style.scss";

interface Props {}

const AuthPage: FunctionComponent<Props> = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const [updating, setUpdate] = useState(false);

  const updateError = useCallback((msg: string) => {
    setError(msg);
    setTimeout(() => setError(""), 2000);
  }, []);

  const onSuccess = useReduxActionFunction(siteAuthSuccess);

  const authState = useReduxStore((s) => s.site.auth);

  const onError = useCallback(() => {
    setUpdate(false);
    updateError("Login Failed");
  }, [updateError]);

  if (authState) {
    return <Redirect to="/"></Redirect>;
  }

  return (
    <div className="d-flex bg-light h-100 justify-content-center align-items-center">
      <Card className="auth-card shadow">
        <Form
          onSubmit={(e) => {
            e.preventDefault();
            if (!updating) {
              setUpdate(true);
              SystemApi.login(username, password)
                .then(onSuccess)
                .catch(onError);
            }
          }}
        >
          <Card.Body>
            <Form.Group className="mb-5 d-flex justify-content-center">
              <Image width="64" height="64" src={logo}></Image>
            </Form.Group>
            <Form.Group>
              <Form.Control
                disabled={updating}
                name="username"
                type="text"
                placeholder="Username"
                required
                onChange={(e) => setUsername(e.currentTarget.value)}
              ></Form.Control>
            </Form.Group>
            <Form.Group>
              <Form.Control
                disabled={updating}
                name="password"
                type="password"
                placeholder="Password"
                required
                onChange={(e) => setPassword(e.currentTarget.value)}
              ></Form.Control>
            </Form.Group>
            <Collapse in={error.length !== 0}>
              <div>
                <Alert variant="danger" className="m-0">
                  {error}
                </Alert>
              </div>
            </Collapse>
          </Card.Body>
          <Card.Footer>
            <Button type="submit" disabled={updating} block>
              {updating ? (
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

export default AuthPage;
