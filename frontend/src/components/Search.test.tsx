import { describe, it } from "vitest";
import { Search } from "@/components/index";
import { customRender } from "@/tests";

describe("Search Bar", () => {
  it.skip("should render the closed empty state", () => {
    customRender(<Search />);
  });
});
