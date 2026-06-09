module.exports = {
  apps: [
    {
      name: "k-beauty-frontend",
      cwd: "/www/wwwroot/k-beauty-proxy-mall/frontend",
      script: "npm",
      args: "run start:prod",
      interpreter: "none",
      env: {
        NODE_ENV: "production",
        API_PROXY_TARGET: "http://127.0.0.1:8000"
      }
    }
  ]
};
