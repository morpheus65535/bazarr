import { readFile } from "fs/promises";

async function parseConfig(path: string) {
  const config = await readFile(path, "utf8");

  const targetSection = config
    .split("\n\n")
    .filter((section) => section.includes("[auth]"));

  if (targetSection.length === 0) {
    throw new Error("Cannot find [auth] section in config");
  }

  const section = targetSection[0];

  for (const line of section.split("\n")) {
    const matches = line.match(/^apikey.*(?<key>[a-z0-9]{32})$/);
    if (matches) {
      return matches.groups.key;
    }
  }

  throw new Error("Cannot find apikey in config");
}

export async function findApiKey(
  env: Record<string, string>
): Promise<string | undefined> {
  if (env["VITE_API_KEY"] !== undefined) {
    return undefined;
  }

  if (env["VITE_BAZARR_CONFIG_FILE"] !== undefined) {
    const path = env["VITE_BAZARR_CONFIG_FILE"];

    try {
      const apiKey = await parseConfig(path);

      return apiKey;
    } catch (err) {
      console.warn(err.message);
    }
  }

  return undefined;
}
