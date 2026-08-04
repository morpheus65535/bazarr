const ASS_MARKUP = /\{\\[^}]*\}|\\N|\\h/;

const escapeHtml = (text: string) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Only basic formatting toggles ({\i1}, {\b1}, ...) translate to HTML;
// positioning, karaoke and other override tags are dropped.
export const assToHtml = (content: string) =>
  escapeHtml(content)
    .replace(/\\h/g, " ")
    .replace(/\\N|\\n/g, "\n")
    .replace(/\{\\[^}]*\}/g, (block) =>
      Array.from(block.matchAll(/\\(i|b|u|s)([01])/g))
        .map(([, tag, on]) => (on === "1" ? `<${tag}>` : `</${tag}>`))
        .join(""),
    );

export const toRenderable = (content: string) =>
  ASS_MARKUP.test(content) ? assToHtml(content) : content;
