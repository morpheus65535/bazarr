import { createCombineAction } from "./utils";
import { updateBadges } from "./badges";
import { updateLanguagesList } from "./system";

export const bootstrap = createCombineAction(() => [
  updateBadges(),
  updateLanguagesList(),
]);

export * from "./badges";
export * from "./movie";
export * from "./series";
export * from "./system";
export * from "./providers";
