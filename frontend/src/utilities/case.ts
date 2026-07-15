export const toCamelCase = (value: string): string =>
  value.replace(/_(.)/g, (_, char) => char.toUpperCase());

export const toSnakeCase = (value: string): string =>
  value
    .replace(/([A-Z]+)/g, (_, chars) => `_${chars.toLowerCase()}`)
    .replace(/^_/, "");

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" &&
  value !== null &&
  !Array.isArray(value) &&
  !(value instanceof Date) &&
  !(value instanceof File) &&
  !(value instanceof Blob) &&
  !(value instanceof RegExp);

export const camelCaseKeys = <T>(value: T): CamelCaseKeys<T> => {
  if (Array.isArray(value)) {
    return value.map(camelCaseKeys) as CamelCaseKeys<T>;
  }

  if (isPlainObject(value)) {
    const result: Record<string, unknown> = {};

    for (const [key, val] of Object.entries(value)) {
      result[toCamelCase(key)] = camelCaseKeys(val);
    }

    return result as CamelCaseKeys<T>;
  }

  return value as CamelCaseKeys<T>;
};

export const snakeCaseKeys = <T>(value: T): LooseObject => {
  if (Array.isArray(value)) {
    return value.map(snakeCaseKeys);
  }

  if (isPlainObject(value)) {
    const result: Record<string, unknown> = {};

    for (const [key, val] of Object.entries(value)) {
      result[toSnakeCase(key)] = snakeCaseKeys(val);
    }

    return result;
  }

  return value as LooseObject;
};
