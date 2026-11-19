import { vi } from "vitest";
import queryClient from "@/apis/queries";
import { QueryKeys } from "@/apis/queries/keys";
import { createDefaultReducer } from "./reducer";

describe("sports socket events", () => {
  it.each([
    ["sports-league", [QueryKeys.SportsLeagues]],
    [
      "sports-event-wanted",
      [QueryKeys.SportsLeagues, QueryKeys.SportsEvents, QueryKeys.Wanted],
    ],
    [
      "sports-event-blacklist",
      [QueryKeys.SportsLeagues, QueryKeys.SportsEvents, QueryKeys.Blacklist],
    ],
    [
      "sports-event-history",
      [QueryKeys.SportsLeagues, QueryKeys.SportsEvents, QueryKeys.History],
    ],
  ])("invalidates %s after a live change", (event, key) => {
    const invalidate = vi
      .spyOn(queryClient, "invalidateQueries")
      .mockResolvedValue();
    const reducer = createDefaultReducer().find((item) => item.key === event);

    expect(reducer).toBeDefined();
    reducer?.any?.();
    expect(invalidate).toHaveBeenCalledWith({ queryKey: key });

    invalidate.mockRestore();
  });
});
