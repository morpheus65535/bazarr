import { Entrance } from "index";
import {} from "jest";
import ReactDOM from "react-dom";

it("renders", () => {
  const div = document.createElement("div");
  ReactDOM.render(<Entrance />, div);
  ReactDOM.unmountComponentAtNode(div);
});
