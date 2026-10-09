import { faTrash } from "@fortawesome/free-solid-svg-icons";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen, waitFor } from "@/tests";
import ToolboxButton, { ToolboxMutateButton } from "./Button";

describe("ToolboxButton", () => {
  it("renders the button and handles click", async () => {
    const onClick = vitest.fn();

    customRender(
      <ToolboxButton icon={faTrash} onClick={onClick}>
        Delete
      </ToolboxButton>,
    );

    const button = screen.getByRole("button", { name: "Delete" });
    expect(button).toBeInTheDocument();

    await userEvent.click(button);

    expect(onClick).toHaveBeenCalledTimes(1);
  });
});

describe("ToolboxMutateButton", () => {
  it("calls the promise and invokes onSuccess", async () => {
    const promise = vitest.fn().mockResolvedValue("done");
    const onSuccess = vitest.fn();

    customRender(
      <ToolboxMutateButton
        icon={faTrash}
        promise={promise}
        onSuccess={onSuccess}
      >
        Run
      </ToolboxMutateButton>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Run" }));

    await waitFor(() => expect(promise).toHaveBeenCalledTimes(1));
    expect(onSuccess).toHaveBeenCalledWith("done");
  });
});
