import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { useFileSystem } from "@/apis/hooks";
import { customRender, fireEvent, screen } from "@/tests";
import { FileBrowser } from "./FileBrowser";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useFileSystem: vitest.fn(),
  };
});

const mockUseFileSystem = vitest.mocked(useFileSystem);

const tree: FileTree[] = [
  { path: "/some/path/folder1/", name: "folder1", children: true },
  { path: "/some/path/file.txt", name: "file.txt", children: false },
];

describe("FileBrowser", () => {
  it("renders with the default value and opens on focus", async () => {
    mockUseFileSystem.mockReturnValue({
      data: tree,
    } as unknown as ReturnType<typeof useFileSystem>);

    customRender(
      <FileBrowser type="bazarr" defaultValue="/some/path/" label="Browse" />,
    );

    const input = screen.getByRole("combobox");
    expect(input).toHaveValue("/some/path/");
    expect(mockUseFileSystem).toHaveBeenCalledWith(
      "bazarr",
      "/some/path/",
      false,
    );

    await userEvent.click(input);

    expect(mockUseFileSystem).toHaveBeenLastCalledWith(
      "bazarr",
      "/some/path/",
      true,
    );
  });

  it("selects a folder and updates the value", async () => {
    mockUseFileSystem.mockReturnValue({
      data: tree,
    } as unknown as ReturnType<typeof useFileSystem>);
    const onChange = vitest.fn();

    customRender(
      <FileBrowser
        type="bazarr"
        defaultValue="/some/path/"
        onChange={onChange}
        label="Browse"
      />,
    );

    const input = screen.getByRole("combobox");
    await userEvent.click(input);

    const option = await screen.findByText("/some/path/folder1/");
    await userEvent.click(option);

    expect(input).toHaveValue("/some/path/folder1/");
    expect(onChange).toHaveBeenCalledWith("/some/path/folder1/");
  });

  it("updates the path when the user types a new value", async () => {
    mockUseFileSystem.mockReturnValue({
      data: tree,
    } as unknown as ReturnType<typeof useFileSystem>);
    const onChange = vitest.fn();

    customRender(
      <FileBrowser
        type="bazarr"
        defaultValue="/some/path/"
        onChange={onChange}
        label="Browse"
      />,
    );

    const input = screen.getByRole("combobox");
    await userEvent.clear(input);
    await userEvent.type(input, "/new/path/");

    expect(input).toHaveValue("/new/path/");
    expect(onChange).toHaveBeenCalledWith("/new/path/");
  });

  it("disables the file system query on blur", async () => {
    mockUseFileSystem.mockReturnValue({
      data: tree,
    } as unknown as ReturnType<typeof useFileSystem>);

    customRender(
      <FileBrowser type="bazarr" defaultValue="/some/path/" label="Browse" />,
    );

    const input = screen.getByRole("combobox");
    await userEvent.click(input);

    expect(mockUseFileSystem).toHaveBeenLastCalledWith(
      "bazarr",
      "/some/path/",
      true,
    );

    fireEvent.blur(input);

    expect(mockUseFileSystem).toHaveBeenLastCalledWith(
      "bazarr",
      "/some/path/",
      false,
    );
  });
});
