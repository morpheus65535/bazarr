import { camelCase, snakeCase } from "lodash";

export const toCamelCase = (value: string): string => camelCase(value);

export const toSnakeCase = (value: string): string => snakeCase(value);

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
      result[camelCase(key)] = camelCaseKeys(val);
    }

    return result as CamelCaseKeys<T>;
  }

  return value as CamelCaseKeys<T>;
};

export function snakeCaseKeys<T>(value: T[]): Record<string, unknown>[];
export function snakeCaseKeys<T>(value: T): Record<string, unknown>;
export function snakeCaseKeys<T>(
  value: T | T[],
): Record<string, unknown> | Record<string, unknown>[] {
  if (Array.isArray(value)) {
    return value.map(snakeCaseKeys);
  }

  if (isPlainObject(value)) {
    const result: Record<string, unknown> = {};

    for (const [key, val] of Object.entries(value)) {
      result[snakeCase(key)] = snakeCaseKeys(val);
    }

    return result;
  }

  return value as Record<string, unknown>;
}
