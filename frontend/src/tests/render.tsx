import { FunctionComponent } from "react";
import { render } from ".";

export interface RenderTestCase {
  name: string;
  ui: FunctionComponent;
}

export function renderTest(name: string, cases: RenderTestCase[]) {
  describe(name, () => {
    cases.forEach((element) => {
      it(`${element.name.toLowerCase()} should render`, () => {
        render(<element.ui />);
      });
    });
  });
}
