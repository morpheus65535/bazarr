// A workaround of built-in hooks in React-Router v6
// https://gist.github.com/rmorse/426ffcc579922a82749934826fa9f743

import { unstable_usePrompt as useUnstablePrompt } from "react-router";

// TODO: Replace with Mantine's confirmation modal
export function usePrompt(when: boolean, message: string) {
  useUnstablePrompt({ when, message });
}
