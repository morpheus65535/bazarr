import { ReactNode } from "react";
import {
  onlineManager,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import { vi } from "vitest";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import { useSettingsMutation } from "./system";

it("refreshes sports lists when settings are saved", async () => {
  onlineManager.setOnline(true);
  const client = new QueryClient();
  const invalidate = vi.spyOn(client, "invalidateQueries").mockResolvedValue();
  const update = vi
    .spyOn(api.system, "updateSettings")
    .mockResolvedValue(undefined);
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  const { result } = renderHook(() => useSettingsMutation({ silent: true }), {
    wrapper,
  });

  await act(async () => {
    await result.current.mutateAsync({
      "settings-sportarr-excluded_tags": ["UFC"],
    });
  });

  expect(invalidate).toHaveBeenCalledWith({
    queryKey: [QueryKeys.SportsLeagues],
  });
  expect(invalidate).toHaveBeenCalledWith({
    queryKey: [QueryKeys.SportsEvents],
  });
  update.mockRestore();
  invalidate.mockRestore();
  onlineManager.setOnline(false);
});
