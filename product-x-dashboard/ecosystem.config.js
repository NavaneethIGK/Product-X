module.exports = {
  apps: [
    {
      name: "product-x-dashboard",
      script: "npm",
      args: "run preview -- --host 0.0.0.0 --port 5000",
      cwd: "/home/ubunut/Product X/product-x-dashboard",
      env: {
        NODE_ENV: "production"
      },
      error_file: "./logs/err.log",
      out_file: "./logs/out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z"
    }
  ]
}
