import { describe, expect, it } from "vitest";
import { customRender, screen } from "@/tests";
import Lazy from "./Lazy";

function Child() {
  return <div>Loaded</div>;
}

describe("Lazy", () => {
  it("renders its children", () => {
    customRender(
      <Lazy>
        <Child />
      </Lazy>,
    );

    expect(screen.getByText("Loaded")).toBeInTheDocument();
  });
});
