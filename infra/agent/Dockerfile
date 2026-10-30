FROM docker:29.7.2-cli@sha256:3f4743208d2338c934d7b8bcfbe1bb54c0b2355c510ad5e0f31c0c4a54bd704e AS dockercli
FROM jenkins/inbound-agent:jdk21@sha256:06e31b0c2291f8150a528131179f2317737bace173dce00a96cec94671c887f9
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/* && usermod -aG root jenkins
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
COPY start.sh /usr/local/bin/start-asdp-agent
RUN chmod 755 /usr/local/bin/start-asdp-agent && git config --system --add safe.directory /opt/source
USER jenkins
ENTRYPOINT ["/usr/local/bin/start-asdp-agent"]
