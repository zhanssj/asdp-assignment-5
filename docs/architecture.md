# Architecture

The FastAPI layer reads a bounded upload and delegates to a framework-independent CSV/statistics module. The browser interface is served from the same process. It preserves the Assignment 3 interaction and API field names while the implementation is Python-based, as required by Assignment 5.

The controller, inbound build agent and deployed application are separate containers. Only the build agent receives the Docker socket. Jenkins starts authenticated, with a generated local administrator password, and uses a persistent home volume. The bootstrap creates the agent and a Pipeline-from-SCM job whose script path is `infra/Jenkinsfile`.

Tests execute inside the test target, without the Docker socket or Jenkins credentials. A separate runtime target contains the application and runtime dependencies, runs as a non-root user and embeds the source commit. The pipeline validates a temporary runtime container and then uses the same image for local deployment. Deployment checks ownership labels before replacing containers and restores the previous service on verification failure.

All configuration and scripts related to images, dependencies, builds and delivery reside in `infra/`. Generated reports and local credentials are ignored by Git. The source archive and build context exclude those credentials. Local SCM mode is an explicit alternative for a classroom demonstration before repository publication.
