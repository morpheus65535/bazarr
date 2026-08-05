import client from "./client";

type UrlTestResponse =
  | {
      status: true;
      version: string;
      code: number;
    }
  | {
      status: false;
      error: string;
      code: number;
    };

class RequestUtils {
  async urlTest(protocol: string, url: string, params?: unknown) {
    try {
      const result = await client.axios.get<UrlTestResponse>(
        `../test/${protocol}/${url}api/system/status`,
        { params },
      );
      const { data } = result;
      if (data.status && data.version) {
        return data;
      }
      throw new Error("Cannot get response, fallback to v3 api");
    } catch {
      const result = await client.axios.get<UrlTestResponse>(
        `../test/${protocol}/${url}api/v3/system/status`,
        { params },
      );
      return result.data;
    }
  }

  async providerUrlTest(protocol: string, url: string, params?: unknown) {
    const result = await client.axios.get<UrlTestResponse>(
      `../test/${protocol}/${url}status`,
      { params },
    );
    const { data } = result;
    if (data.status && data.version) {
      return data;
    }
    return result.data;
  }
}

const requestUtils = new RequestUtils();
export default requestUtils;

// Maps the frontend list query state to the snake_case params expected by the
// backend list endpoints (/series, /movies). Undefined values are dropped by
// axios when building the query string.
export const buildListParams = (
  params: Parameter.ListQuery,
): Record<string, unknown> => {
  const { start, length, sortBy, sortOrder, filters } = params;
  const result: Record<string, unknown> = { start, length };

  if (sortBy) {
    result.sort_by = sortBy;
  }
  if (sortOrder) {
    result.sort_order = sortOrder;
  }
  if (filters) {
    if (filters.monitored !== undefined) {
      result.monitored = filters.monitored ? "true" : "false";
    }
    if (filters.missing !== undefined) {
      result.missing = filters.missing ? "true" : "false";
    }
    if (filters.profileId !== undefined) {
      // 0 means "items without a languages profile"
      result.profileid = filters.profileId === 0 ? "none" : filters.profileId;
    }
    if (filters.audioLanguage !== undefined) {
      result.audio_language = filters.audioLanguage;
    }
    if (filters.tags && filters.tags.length > 0) {
      result.tags = filters.tags;
    }
  }

  return result;
};
