# Smart City Sensor Data Analyzer

ASDP Assignment 5 continues Assignment 3's Scientific CSV Data Analyzer theme in **Python**, with a working local **Jenkins + Docker CI/CD** setup. The application previews sensor CSV files, analyzes a numeric column, plots measurements and exports JSON/summary CSV. Environmental fixtures are synthetic examples, not measurements collected from a city deployment.

## Local Jenkins

Prerequisite: Docker Desktop running **Linux containers**, with ports **8081** and **8000** available. No separate host Python or Java installation is needed.

From the project root in PowerShell:

```powershell
.\infra\scripts\Start-Local.ps1
```

Open <http://localhost:8081/>. Username: `admin`. Read the generated password from `infra/.local/admin-password.txt`. It is deliberately excluded from Git. Open the job **asdp-assignment-5** and select **Build Now** for the first run. Jenkins loads **`infra/Jenkinsfile`** from the configured source repository. A successful pipeline deploys the analyzer at <http://localhost:8000/>.

To set another repository URL, use:

```powershell
.\infra\scripts\Start-Local.ps1 -RepositoryUrl 'https://github.com/zhanssj/asdp-assignment-5.git'
```

For offline classroom verification against the local Git repository, use `-RepositoryUrl 'file:///opt/source'`. The local repository must contain a committed `main` branch. Both containers have a read-only source mount; enabling local checkout is limited to this explicit mode. Re-run the startup script to change the configured source. Jenkins checks it every minute after the first pipeline run; polling only builds when a revision changes and may combine commits received between polls.

The controller uses zero build executors. A separate inbound agent performs the builds over a private Docker network and accesses the local Docker engine. This is a trusted, single-user demonstration setup; only run project code you trust. Jenkins and the deployed application bind to localhost. Named volumes retain job configuration, history and agent data across container restarts.

Stop Jenkins and its agent without deleting their data:

```powershell
docker compose --env-file infra/.env -f infra/compose.yaml stop
```

The independently deployed analyzer keeps running; stop it with `docker stop asdp5-analyzer`. Start it again with `docker start asdp5-analyzer`, or run the pipeline. No Docker Hub account is required.

## Pipeline

1. **Checkout:** record the exact source commit.
2. **Unit and API tests:** build a test environment, run pytest and publish JUnit XML. A test failure blocks later stages.
3. **Build application image:** build the runtime image tagged with the source commit.
4. **Container smoke test:** start a temporary container; verify health, the browser page, input hash and independently known statistical results over real HTTP.
5. **Deploy local test service:** replace only this assignment's service, verify it and restore the previous service if validation fails.

JUnit XML, source revision and JSON smoke/deployment evidence are retained as Jenkins artifacts. Temporary test containers are removed. The application runs as UID 10001. Its `/health` endpoint and JSON analysis export identify the source commit. This demonstrates local continuous deployment; it does not establish production availability or big-data performance.

## Run tests separately

```powershell
.\infra\scripts\Invoke-Tests.ps1
```

This uses the same Docker test target as Jenkins and writes `infra/build/junit.xml`. Numerical tests use independently known results, including `20,22,24,26,28`: count 5, mean/median 24 and sample deviation `sqrt(10)`.

## Project structure

```text
app/                 Python API, scientific module and browser assets
tests/               Numerical, CSV contract and API tests
examples/            Synthetic environmental/sensor CSV fixtures
docs/                Architecture and verification notes
infra/
  Dockerfile         Application runtime and test targets
  Dockerfile.dockerignore
  requirements*.lock Pinned Python dependency sets
  Jenkinsfile        Pipeline loaded through Jenkins' custom script path
  compose.yaml       Local Jenkins controller and build agent
  jenkins/           Controller image, plugin versions and bootstrap configuration
  agent/             Build-agent image and startup script
  scripts/           Startup, testing, HTTP verification and deployment
  build/             Generated reports (ignored)
  .local/            Generated local credentials (ignored)
```

All Docker and build configuration lives under **infra**. The project root contains source organization, repository metadata and this README.

## Data and scientific contract

- UTF-8 CSV with optional BOM, comma delimiter, quoted commas/multiline fields; blank physical lines ignored. Whitespace is trimmed in every field, including quoted fields.
- Nonblank unique headers, at least one data record and consistent record width. Limits: 5 MiB, 10,000 records, 50 columns, 2,000 characters per field.
- Finite decimal numbers and scientific notation are supported. NaN, infinity, decimal commas and hexadecimal numbers are rejected. Values use binary double precision; extremely small values may round to zero.
- Blank measurements are excluded and counted. Invalid nonblank measurements produce a logical CSV record/column error. A blank-only column cannot be analyzed.
- Statistics: count, minimum, maximum, arithmetic mean, median and **sample** standard deviation (`n - 1`). Sample deviation is `null` for a single value. Unrepresentable results are rejected.
- Units are labels, not conversions. The chart follows row order, not inferred time, and retains gaps for blanks. JSON exports preserve the exact input SHA-256, exclusions, method, application version and source commit. The browser's summary CSV guards textual spreadsheet formulas.
- Uploads are processed per request, without a persistent dataset archive. This bounded research demonstration is not the thesis's complete big-data storage system.

## API

`GET /health`; `POST /api/datasets/preview` with multipart `file`; `POST /api/analysis` with multipart `file`, `column`, optional `unit`. Validation returns JSON `message` with HTTP 400, or 413 for an oversized CSV.

```powershell
curl.exe -F 'file=@examples/temperature.csv' -F 'column=temperature_C' http://localhost:8000/api/analysis
```

Measured execution details are recorded in [docs/verification.md](docs/verification.md).

## Sources and origin

The interface and CSV analyzer concept continue <https://github.com/zhanssj/asdp-assignment-3>; the backend and delivery configuration are implemented for Assignment 5. Original project code is MIT licensed. Dependencies retain their licenses.

- <https://www.jenkins.io/doc/book/installing/docker/>
- <https://www.jenkins.io/doc/book/pipeline/>
- <https://www.jenkins.io/doc/book/security/controller-isolation/>
- <https://docs.docker.com/build/building/best-practices/>
- <https://fastapi.tiangolo.com/tutorial/testing/>
