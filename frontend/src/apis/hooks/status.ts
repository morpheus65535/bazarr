import { useIsMutating } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";

export const useIsAnyActionRunning = () =>
  useIsMutating({
    mutationKey: [QueryKeys.Actions],
  }) > 0;

export const useIsMovieActionRunning = () =>
  useIsMutating({
    mutationKey: [QueryKeys.Actions, QueryKeys.Movies],
  }) > 0;

export const useIsSeriesActionRunning = () =>
  useIsMutating({
    mutationKey: [QueryKeys.Actions, QueryKeys.Series],
  }) > 0;

export const useIsAnyMutationRunning = () => useIsMutating() > 0;
