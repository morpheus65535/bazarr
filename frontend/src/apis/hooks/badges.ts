import { useQuery } from "react-query";
import { BadgesApi } from "..";

export function useBadges() {
  return useQuery(["system", "badges"], () => BadgesApi.all());
}
