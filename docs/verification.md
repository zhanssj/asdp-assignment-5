# Verification on 30 October 2026

Jenkins **2.580.2**, running locally in Docker Desktop with a separate inbound agent, checked out GitHub commit `7a4030f91a9f0b5db095b006ab2c5d691fdbaef6`. Build **#1 finished SUCCESS**. All five required/project stages passed: Checkout, Unit and API tests, Build application image, Container smoke test, and Deploy local test service. Artifact retention and cleanup also passed.

The JUnit report records **63 tests**, zero failures and zero errors. These cover numerical reference cases, single/constant/negative samples, large offsets and magnitudes, subnormal median values, CSV dialect and resource limits, missingness, multipart API behavior and provenance.

The temporary image and deployed application both passed real HTTP checks. The reference values `20,22,24,26,28` produced mean **24**, median **24**, sample standard deviation **3.1622776601683795**, and SHA-256 **3ec1f43179e74ad4a98ef83e87cd257aba16d0dfb6244e387b2c7e66020dfeb9**. `/health` returned the same source commit used to tag the image.

A separate deployment-recovery check deliberately requested an incorrect source revision. Verification rejected the replacement and restored the original container with the original healthy response. This exercised the rollback path, not only its configuration.

The agent was subsequently extended with Docker Buildx so subsequent runs use BuildKit and its Dockerfile-specific context exclusions. Runtime/test dependencies and container base digests are pinned; installed Jenkins plugin versions are recorded in `infra/jenkins/plugins.txt`.

Build **#2** was automatically triggered by SCM polling after commit `a671e30472260c6e3deee5859f1ca9ee97b122db` was published. It also finished **SUCCESS**, with all **63 tests passing**, BuildKit image construction, HTTP verification and replacement of the local test service. This verifies automatic triggering and a repeated deployment, in addition to the first manual build.

Live evidence: <http://localhost:8081/job/asdp-assignment-5/>. Jenkins retains JUnit XML, the source commit and JSON smoke/deployment reports as build artifacts. Local services are available while this computer and Docker are running. Screenshots and bilingual submission reports are stored in the separate Assignment 5 document folder.

The demonstration validates local CI/CD and bounded CSV analysis. It does not establish production reliability, terabyte-scale performance or the thesis's storage-policy results.
