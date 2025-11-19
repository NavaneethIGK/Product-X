module.exports = {
  apps: [
    {
      name: "copilot-backend",
      script: "python3",
      args: "copilot_backend.py",
      cwd: "/home/ubuntu/Product-X",
      interpreter: "/usr/bin/python3",
      env: {
        PYTHONUNBUFFERED: 1,
        PATH: "/usr/local/bin:/usr/bin:/bin"
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
