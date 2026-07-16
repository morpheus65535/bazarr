import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import PageControl from "./PageControl";

describe("PageControl", () => {
  it("renders the pagination range", () => {
    customRender(
      <PageControl
        count={5}
        index={0}
        size={10}
        total={50}
        goto={vitest.fn()}
      />,
    );

    expect(screen.getByText("Show 1 to 10 of 50 entries")).toBeInTheDocument();
  });

  it("renders zero range when total is empty", () => {
    customRender(
      <PageControl
        count={1}
        index={0}
        size={10}
        total={0}
        goto={vitest.fn()}
      />,
    );

    expect(screen.getByText("Show 0 to 0 of 0 entries")).toBeInTheDocument();
  });

  it("hides pagination when count is 1 or less", () => {
    customRender(
      <PageControl
        count={1}
        index={0}
        size={10}
        total={10}
        goto={vitest.fn()}
      />,
    );

    expect(screen.queryByRole("button", { name: "1" })).not.toBeInTheDocument();
  });

  it("shows pagination when count is greater than 1", () => {
    customRender(
      <PageControl
        count={3}
        index={0}
        size={10}
        total={30}
        goto={vitest.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "1" })).toBeInTheDocument();
  });

  it("calls goto with the zero-based page index", async () => {
    const goto = vitest.fn();
    customRender(
      <PageControl count={3} index={0} size={10} total={30} goto={goto} />,
    );

    await userEvent.click(screen.getByRole("button", { name: "2" }));

    expect(goto).toHaveBeenCalledWith(1);
  });
});
