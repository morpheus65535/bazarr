const { createProxyMiddleware } = require("http-proxy-middleware");

const target = process.env["REACT_APP_PROXY_URL"];
const allowWs = process.env["REACT_APP_ALLOW_WEBSOCKET"] === "true";
const secure = process.env["REACT_APP_PROXY_SECURE"] === "true";

module.exports = function (app) {
  app.use(
    createProxyMiddleware(["/api", "/images", "/test", "/bazarr.log"], {
      target,
      changeOrigin: true,
      secure,
    })
  );
  app.use(
    createProxyMiddleware("/api/socket.io", {
      target,
      ws: allowWs,
      changeOrigin: true,
      secure,
      logLevel: "error",
    })
  );
};
