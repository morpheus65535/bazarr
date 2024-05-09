import { Component, PropsWithChildren } from "react";
import UIError from "@/pages/errors/UIError";

interface State {
  error: Error | null;
}

class ErrorBoundary extends Component<PropsWithChildren, State> {
  constructor(props: object) {
    super(props);
    this.state = { error: null };
  }

  componentDidCatch(error: Error) {
    this.setState({ error });
  }

  render() {
    const { children } = this.props;
    const { error } = this.state;
    if (error) {
      return <UIError error={error}></UIError>;
    }

    return children;
  }
}

export default ErrorBoundary;
