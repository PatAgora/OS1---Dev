module.exports = {
  apps: [
    {
      name: 'os1-webapp',
      script: 'python3',
      args: '-m flask run --host=0.0.0.0 --port=5000',
      env: {
        FLASK_APP: 'app.py',
        FLASK_DEBUG: '1',
        PYTHONUNBUFFERED: '1',
        OPENAI_API_KEY: process.env.OPENAI_API_KEY || ''
      },
      watch: false,
      instances: 1,
      exec_mode: 'fork',
      cwd: '/home/user/webapp'
    }
  ]
}
