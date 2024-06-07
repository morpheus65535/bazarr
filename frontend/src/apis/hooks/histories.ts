import { useQuery } from "react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

export function useHistoryStats(
  time: History.TimeFrameOptions,
  action: History.ActionOptions | null,
  provider: System.Provider | null,
  language: Language.Info | null,
) {
  return useQuery(
    [QueryKeys.System, QueryKeys.History, { time, action, provider, language }],
    () =>
      api.history.stats(
        time,
        action ?? undefined,
        provider?.name,
        language?.code2,
      ),
  );
}
