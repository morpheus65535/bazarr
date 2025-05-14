export const capitalize = (string: string) => {
  return string
    ? string.charAt(0).toUpperCase() + string.slice(1).toLowerCase()
    : "";
};
