module.exports = {
  apps: [
    {
      name: "dashboard",
      script: "npm",
      args: "run dev",
      cwd: "/home/ubuntu/Product\\ X/product-x-dashboard",
      env: {
        NODE_ENV: "development"
      },
      error_file: "./logs/err.log",
      out_file: "./logs/out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z"
    }
  ]
}
