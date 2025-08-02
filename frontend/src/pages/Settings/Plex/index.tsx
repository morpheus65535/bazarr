import { FunctionComponent, useState, useEffect } from "react";
import axios from "axios";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Number,
  Section,
  Text,
} from "@/pages/Settings/components";
import { plexEnabledKey } from "@/pages/Settings/keys";

type PlexServer = {
  name: string;
  address: string;
  port: string;
  uri: string;
  local: string;
  ssl: boolean;
};

const SettingsPlexView: FunctionComponent = () => {
  const [authenticated, setAuthenticated] = useState(false);
  const [servers, setServers] = useState<PlexServer[]>([]);
  const [selectedServer, setSelectedServer] = useState<PlexServer | null>(null);

  useEffect(() => {
    // Check if authenticated and fetch servers
    axios
      .get("/api/plex/servers")
      .then((res) => {
        if (res.data.servers) {
          setAuthenticated(true);
          setServers(res.data.servers);
        }
      })
      .catch(() => setAuthenticated(false));
  }, []);

  const handleAuthenticate = () => {
    window.location.href = "/api/plex/oauth/login";
  };

  const handleSelectServer = (e: any) => {
    const idx = e.target.value;
    const server = servers[idx];
    setSelectedServer(server);
    // Auto-fill host/port/ssl
    axios.post("/api/plex/server", {
      address: server.address,
      port: server.port,
      ssl: server.ssl,
    });
  };

  return (
    <Layout name="Interface">
      <Section header="Use Plex operations">
        <Check label="Enabled" settingKey={plexEnabledKey}></Check>
        <div style={{ margin: "10px 0" }}>
          {!authenticated ? (
            <button
              onClick={handleAuthenticate}
              style={{
                padding: "8px 16px",
                background: "#3572b0",
                color: "white",
                border: "none",
                borderRadius: "4px",
              }}
            >
              Authenticate with Plex.tv
            </button>
          ) : (
            <div>
              <label htmlFor="plex-server-select">Select Plex Server:</label>
              <select
                id="plex-server-select"
                onChange={handleSelectServer}
                style={{ marginLeft: "10px" }}
              >
                <option value="">-- Select --</option>
                {servers.map((srv, idx) => (
                  <option key={srv.uri} value={idx}>
                    {srv.name} ({srv.address}:{srv.port})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </Section>
      <CollapseBox settingKey={plexEnabledKey}>
        <Section header="Host">
          <Text label="Address" settingKey="settings-plex-ip"></Text>
          <Number
            label="Port"
            settingKey="settings-plex-port"
            defaultValue={32400}
          ></Number>
          <Message>Hostname or IPv4 Address</Message>
          <Text label="API Token" settingKey="settings-plex-apikey"></Text>
          <Check label="SSL" settingKey="settings-plex-ssl"></Check>
        </Section>
        <Section header="Movie library">
          <Text
            label="Name of the library"
            settingKey="settings-plex-movie_library"
          ></Text>
          <Check
            label="Mark the movie as recently added after downloading subtitles"
            settingKey="settings-plex-set_movie_added"
          ></Check>
          <Check
            label="Scan library for new files after downloading subtitles"
            settingKey="settings-plex-update_movie_library"
          ></Check>
          <Message>Can be helpful for remote media files</Message>
        </Section>
        <Section header="Series library">
          <Text
            label="Name of the library"
            settingKey="settings-plex-series_library"
          ></Text>
          <Check
            label="Mark the episode as recently added after downloading subtitles"
            settingKey="settings-plex-set_episode_added"
          ></Check>
          <Check
            label="Scan library for new files after downloading subtitles"
            settingKey="settings-plex-update_series_library"
          ></Check>
          <Message>Can be helpful for remote media files</Message>
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsPlexView;
