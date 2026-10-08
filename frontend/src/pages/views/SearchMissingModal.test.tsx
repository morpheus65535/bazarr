import { UseMutationResult } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { customRender, screen } from "@/tests";
import { BulkSelection } from "@/utilities/bulkSelection";
import { BulkActionBarSearchButton } from "./BulkActionBar";
import { SearchMissingConfig } from "./SearchMissingModal";

const buildConfig = (
  mutateAsync = vi.fn().mockResolvedValue(undefined),
  whisperFallbackOption = false,
): SearchMissingConfig => ({
  mutation: { mutateAsync } as unknown as UseMutationResult<
    void,
    unknown,
    FormType.SearchMissing
  >,
  unit: { singular: "movie", plural: "movies" },
  whisperFallbackOption,
});

const selectionOf = (...ids: number[]) =>
  ({ selectedIds: new Set(ids) }) as unknown as BulkSelection;

describe("BulkActionBarSearchButton", () => {
  it("is disabled until something is selected", () => {
    customRender(
      <BulkActionBarSearchButton
        selection={selectionOf()}
        config={buildConfig()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Search Selected (0)" }),
    ).toBeDisabled();
  });

  it("explains it runs as one task that can be cancelled in the Jobs Manager", async () => {
    customRender(
      <BulkActionBarSearchButton
        selection={selectionOf(1, 2, 3)}
        config={buildConfig()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Search Selected (3)" }),
    );

    expect(await screen.findByText("3 movies")).toBeInTheDocument();
    expect(screen.getByText("Runs as a single task")).toBeInTheDocument();
    expect(screen.getByText(/cancel the task there/i)).toBeInTheDocument();
    expect(screen.queryByText(/restarting bazarr/i)).not.toBeInTheDocument();
  });

  it("searches exactly the selected ids", async () => {
    const mutateAsync = vi.fn().mockResolvedValue(undefined);
    customRender(
      <BulkActionBarSearchButton
        selection={selectionOf(4, 9)}
        config={buildConfig(mutateAsync)}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Search Selected (2)" }),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Search 2 movies" }),
    );

    // No Whisper option for this config, so no whisperFallback is sent.
    expect(mutateAsync).toHaveBeenCalledWith({ ids: [4, 9] });
    expect(mutateAsync.mock.calls[0][0]).not.toHaveProperty("whisperFallback");
  });

  it("does not offer the Whisper option unless the config asks for it", async () => {
    customRender(
      <BulkActionBarSearchButton
        selection={selectionOf(1)}
        config={buildConfig()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Search Selected (1)" }),
    );
    await screen.findByText("1 movie");

    expect(
      screen.queryByLabelText(/whisper fallback/i),
    ).not.toBeInTheDocument();
  });

  it("sends whisperFallback: true by default when the option is offered", async () => {
    const mutateAsync = vi.fn().mockResolvedValue(undefined);
    customRender(
      <BulkActionBarSearchButton
        selection={selectionOf(5)}
        config={buildConfig(mutateAsync, true)}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Search Selected (1)" }),
    );
    expect(await screen.findByLabelText(/whisper fallback/i)).toBeChecked();
    await userEvent.click(
      screen.getByRole("button", { name: "Search 1 movie" }),
    );

    expect(mutateAsync).toHaveBeenCalledWith({
      ids: [5],
      whisperFallback: true,
    });
  });

  it("sends whisperFallback: false when the box is unchecked", async () => {
    const mutateAsync = vi.fn().mockResolvedValue(undefined);
    customRender(
      <BulkActionBarSearchButton
        selection={selectionOf(5, 6)}
        config={buildConfig(mutateAsync, true)}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Search Selected (2)" }),
    );
    await userEvent.click(await screen.findByLabelText(/whisper fallback/i));
    await userEvent.click(
      screen.getByRole("button", { name: "Search 2 movies" }),
    );

    expect(mutateAsync).toHaveBeenCalledWith({
      ids: [5, 6],
      whisperFallback: false,
    });
  });
});
