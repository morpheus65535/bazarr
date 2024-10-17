import { describe, it } from "vitest";
import { Search } from "@/components/index";
import { render } from "@/tests";

describe("Search Bar", () => {
  it.skip("should render the closed empty state", () => {
    render(<Search />);
  });
});
