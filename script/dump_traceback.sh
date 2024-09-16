#!/bin/sh

python_pid=$(ps aux | grep '[p]ython' | awk '{print $1}' | head -n 1)

echo "python pid is: $python_pid, going to send SIGUSR1 to the process to get traceback"
kill -SIGUSR1 $python_pid
echo "done, goodbye!"
