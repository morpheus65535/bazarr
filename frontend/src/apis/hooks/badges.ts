import { useQuery } from "react-query";
import api from "../raw";

export function useBadges() {
  return useQuery(["system", "badges"], () => api.badges.all());
}
