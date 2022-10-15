/* eslint-disable no-console */
/// <reference types="node" />

import { readFile } from "fs/promises";

class ConfigReader {
  config?: string;

  constructor() {
    this.config = undefined;
  }

  async open(path: string) {
    try {
      this.config = await readFile(path, "utf8");
    } catch (err) {
      // We don't want to catch the error here, handle it on getValue method
    }
  }

  getValue(sectionName: string, fieldName: string) {
    if (!this.config) {
      throw new Error("Cannot find config to read");
    }
    const targetSection = this.config
      .split("\n\n")
      .filter((section) => section.includes(`[${sectionName}]`));

    if (targetSection.length === 0) {
      throw new Error(`Cannot find [${sectionName}] section in config`);
    }

    const section = targetSection[0];

    for (const line of section.split("\n")) {
      const matched = line.startsWith(fieldName);
      if (matched) {
        const results = line.split("=");
        if (results.length === 2) {
          const key = results[1].trim();
          return key;
        }
      }
    }

    throw new Error(`Cannot find ${fieldName} in config`);
  }
}

export default async function overrideEnv(env: Record<string, string>) {
  const configPath = env["VITE_BAZARR_CONFIG_FILE"];

  if (configPath === undefined) {
    return;
  }

  const reader = new ConfigReader();
  await reader.open(configPath);

  if (env["VITE_API_KEY"] === undefined) {
    try {
      const apiKey = reader.getValue("auth", "apikey");

      console.log(`Using API key: ${apiKey}`);

      env["VITE_API_KEY"] = apiKey;
      process.env["VITE_API_KEY"] = apiKey;
    } catch (err) {
      throw new Error(
        `No API key found, please run the backend first, (error: ${err.message})`
      );
    }
  }

  if (env["VITE_PROXY_URL"] === undefined) {
    try {
      const port = reader.getValue("general", "port");
      const baseUrl = reader.getValue("general", "base_url");

      const url = `http://127.0.0.1:${port}${baseUrl}`;

      console.log(`Using backend url: ${url}`);

      env["VITE_PROXY_URL"] = url;
      process.env["VITE_PROXY_URL"] = url;
    } catch (err) {
      throw new Error(
        `No proxy url found, please run the backend first, (error: ${err.message})`
      );
    }
  }
}
