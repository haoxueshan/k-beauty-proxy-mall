module.exports = {
  apps: [
    {
      name: "k-beauty-frontend",
      cwd: "/www/wwwroot/k-beauty-proxy-mall/frontend",
      script: "node_modules/next/dist/bin/next",
      args: "start --hostname 127.0.0.1 --port 3000",
      env: {
        NODE_ENV: "production"
      }
    }
  ]
};
