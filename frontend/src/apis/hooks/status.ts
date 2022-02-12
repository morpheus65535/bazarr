import { useIsMutating } from "react-query";
import { QueryKeys } from "../queries/keys";

export function useIsAnyActionRunning() {
  return useIsMutating([QueryKeys.Actions]) > 0;
}

export function useIsMovieActionRunning() {
  return useIsMutating([QueryKeys.Actions, QueryKeys.Movies]) > 0;
}

export function useIsSeriesActionRunning() {
  return useIsMutating([QueryKeys.Actions, QueryKeys.Series]) > 0;
}

export function useIsAnyMutationRunning() {
  return useIsMutating() > 0;
}
