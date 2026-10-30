FROM jenkins/jenkins:2.580.2-jdk21@sha256:74401de6a6f92e1afe1b02d1c8e3d0c33f263bfb5275dd8813f9150355f2367b
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY bootstrap.groovy /usr/share/jenkins/ref/init.groovy.d/bootstrap.groovy
USER root
RUN mkdir -p /run/agent-auth && chown jenkins:jenkins /run/agent-auth \
    && git config --system --add safe.directory /opt/source
USER jenkins
