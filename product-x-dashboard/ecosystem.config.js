module.exports = {
  apps: [
    {
      name: "copilot-backend",
      script: "/home/ubuntu/Product-X/run_backend.sh",
      cwd: "/home/ubuntu/Product-X",
      env: {
        PYTHONUNBUFFERED: 1
      },
      error_file: "./logs/backend-err.log",
      out_file: "./logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z"
    },
    {
      name: "dashboard",
      script: "npm",
      args: "run dev",
      cwd: "/home/ubuntu/Product-X/product-x-dashboard",
      env: {
        NODE_ENV: "development"
      },
      error_file: "./logs/dashboard-err.log",
      out_file: "./logs/dashboard-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z"
    }
  ]
}
