import { FunctionComponent } from "react";
import { customRender } from ".";

export interface RenderTestCase {
  name: string;
  ui: FunctionComponent;
  setupEach?: () => void;
}

export function renderTest(name: string, cases: RenderTestCase[]) {
  describe(name, () => {
    cases.forEach((element) => {
      it(`${element.name.toLowerCase()} should render`, () => {
        element.setupEach?.();
        customRender(<element.ui />);
      });
    });
  });
}
