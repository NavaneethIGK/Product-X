module.exports = {
  apps: [
    {
      name: "copilot-backend",
      script: "bash",
      args: "-c 'cd /home/ubuntu/Product-X && python3 copilot_backend.py'",
      env: {
        PYTHONUNBUFFERED: 1
      },
      error_file: "./logs/backend-err.log",
      out_file: "./logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z"
    },
    {
      name: "dashboard",
      script: "bash",
      args: "-c 'cd /home/ubuntu/Product-X/product-x-dashboard && npm run dev'",
      env: {
        NODE_ENV: "development"
      },
      error_file: "./logs/dashboard-err.log",
      out_file: "./logs/dashboard-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z"
    }
  ]
}
