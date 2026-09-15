import { UseMutationResult } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import MutateButton from "./MutateButton";

const makeMutation = (
  mutateAsync: () => Promise<string> = vitest
    .fn()
    .mockResolvedValue("result") as unknown as () => Promise<string>,
) =>
  ({
    mutateAsync,
  }) as unknown as UseMutationResult<string, unknown, string>;

describe("MutateButton", () => {
  it("calls the mutation and onSuccess when clicked", async () => {
    const mutation = makeMutation();
    const onSuccess = vitest.fn();

    customRender(
      <MutateButton
        mutation={mutation}
        args={() => "argument"}
        onSuccess={onSuccess}
      >
        Submit
      </MutateButton>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(mutation.mutateAsync).toHaveBeenCalledWith("argument");
    expect(onSuccess).toHaveBeenCalledWith("result");
  });

  it("calls onError when args returns null", async () => {
    const mutation = makeMutation();
    const onError = vitest.fn();

    customRender(
      <MutateButton mutation={mutation} args={() => null} onError={onError}>
        Submit
      </MutateButton>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(mutation.mutateAsync).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalled();
  });

  it("calls onError when the mutation throws", async () => {
    const mutateAsync = vitest
      .fn()
      .mockRejectedValue(new Error("fail")) as () => Promise<string>;
    const mutation = makeMutation(mutateAsync);
    const onError = vitest.fn();

    customRender(
      <MutateButton
        mutation={mutation}
        args={() => "argument"}
        onError={onError}
      >
        Submit
      </MutateButton>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(mutateAsync).toHaveBeenCalledWith("argument");
    expect(onError).toHaveBeenCalled();
  });
});
