import { useQuery } from "react-query";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useBadges() {
  return useQuery([QueryKeys.system, QueryKeys.badges], () => api.badges.all());
}
