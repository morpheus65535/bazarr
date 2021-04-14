const proxy = require("http-proxy-middleware");

const target = "http://localhost:6767";

module.exports = function (app) {
  app.use(
    proxy(["/api", "/images", "/test", "/bazarr.log"], {
      target,
    })
  );
  app.use(
    proxy("/api/socket.io", {
      target,
      ws: true,
      logLevel: "error",
    })
  );
};
