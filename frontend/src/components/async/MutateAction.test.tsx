import { faSync } from "@fortawesome/free-solid-svg-icons";
import { UseMutationResult } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import MutateAction from "./MutateAction";

function makeMutation(
  mutateAsync: () => Promise<string> = vitest
    .fn()
    .mockResolvedValue("result") as unknown as () => Promise<string>,
) {
  return {
    mutateAsync,
  } as unknown as UseMutationResult<string, unknown, string>;
}

describe("MutateAction", () => {
  it("calls the mutation and onSuccess when clicked", async () => {
    const mutation = makeMutation();
    const onSuccess = vitest.fn();

    customRender(
      <MutateAction
        mutation={mutation}
        args={() => "argument"}
        onSuccess={onSuccess}
        icon={faSync}
        label="Sync"
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Sync" }));

    expect(mutation.mutateAsync).toHaveBeenCalledWith("argument");
    expect(onSuccess).toHaveBeenCalledWith("result");
  });

  it("calls onError when args returns null", async () => {
    const mutation = makeMutation();
    const onError = vitest.fn();

    customRender(
      <MutateAction
        mutation={mutation}
        args={() => null}
        onError={onError}
        icon={faSync}
        label="Sync"
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Sync" }));

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
      <MutateAction
        mutation={mutation}
        args={() => "argument"}
        onError={onError}
        icon={faSync}
        label="Sync"
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Sync" }));

    expect(mutateAsync).toHaveBeenCalledWith("argument");
    expect(onError).toHaveBeenCalled();
  });
});
