#!/bin/sh
set -eu
while [ ! -s /run/agent-auth/secret ]; do sleep 1; done
exec /usr/local/bin/jenkins-agent -url http://jenkins:8080/ \
  -name docker-agent -secret "$(cat /run/agent-auth/secret)" \
  -webSocket -workDir /home/jenkins/agent
