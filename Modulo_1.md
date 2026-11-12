# Module 1 Homework: Docker, SQL & Terraform

> [!NOTE]
> This is a draft carried over from the 2026 cohort. The questions, datasets,
> and deadlines will be updated before the module starts.

In this homework, we'll prepare the environment and practice Docker, SQL, and
Terraform.

When submitting your homework, include a link to your GitHub repository or
another public code-hosting site. Your repository should contain the code and
queries used to solve the homework.

If a solution consists of SQL or shell commands rather than source-code files
(for example, Python files), include those commands in your repository's
`README.md`.

## Question 1. Understanding Docker images

Run Docker with the `python:3.13` image and use `bash` as the entrypoint to
interact with the container:

```bash
docker run -it --rm --entrypoint bash python:3.13
```

The options mean:

- `-it` allocates an interactive terminal.
- `--rm` removes the container when you exit.
- `--entrypoint bash` starts a Bash shell instead of the image's default command.
- `python:3.13` is the image to run.

Once inside the container, check the installed `pip` version:

```bash
pip --version
```

`pip list` displays installed Python packages; it does not report the `pip`
program's version.

- 25.3
- 24.3.1
- 24.2.1
- 23.3.1
- **26.2.2 — observed result; this may vary**

> **Note:** The actual version may differ from these options. Use the value
> reported by your own `pip --version` command.

## Question 2. Understanding Docker networking and docker-compose

Given the following `docker-compose.yaml`, what hostname and port should
pgAdmin use to connect to PostgreSQL?

```yaml
services:
  db:
    container_name: postgres
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: 'postgres'
      POSTGRES_PASSWORD: 'postgres'
      POSTGRES_DB: 'ny_taxi'
    ports:
      - '5433:5432'
    volumes:
      - vol-pgdata:/var/lib/postgresql/data

  pgadmin:
    container_name: pgadmin
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: "pgadmin@pgadmin.com"
      PGADMIN_DEFAULT_PASSWORD: "pgadmin"
    ports:
      - "8080:80"
    volumes:
      - vol-pgadmin_data:/var/lib/pgadmin

volumes:
  vol-pgdata:
    name: vol-pgdata
  vol-pgadmin_data:
    name: vol-pgadmin_data
```

- `postgres:5433`
- `localhost:5432`
- `db:5433`
- `postgres:5432`
- **`db:5432` — correct (recommended)**

**Explanation:** Compose provides service-name DNS on its default network, so
pgAdmin can reach PostgreSQL using the service name `db`. The `container_name`
(`postgres`) may also resolve on that network, but the service name is
recommended.

The port mapping `5433:5432` has the format `HOST_PORT:CONTAINER_PORT`:

- `5433` is the port exposed on the host. A client running outside Docker can
  connect through `localhost:5433`.
- `5432` is PostgreSQL's port inside the container. Since pgAdmin is also
  running in Docker on the same Compose network, it connects to `db:5432`.

If multiple answers are accepted, select either valid hostname with the
container port `5432`.

## Prepare the Data

Download the November 2025 Green Taxi trips dataset:

```bash
wget https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-11.parquet
```

Download the taxi zone lookup dataset as well:

```bash
wget https://github.com/DataTalksClub/nyc-tlc-data/releases/download/misc/taxi_zone_lookup.csv
```

## Question 3. Counting short trips

For trips picked up in November 2025 (from `2025-11-01` inclusive to
`2025-12-01` exclusive), how many had a `trip_distance` of 1 mile or less?

Start the services defined in `docker-compose.yaml` in the background:

```bash
docker compose up -d
```

`docker compose up` creates and starts the declared containers; `-d` runs them
in the background and returns control to the terminal.

Create an `ingest_data.py` script to load the downloaded trips and zone lookup
data into PostgreSQL. The queries below expect the data to be available in the
`green_taxi_trips` and `taxi_zones` tables. Run the script:

```bash
python ingest_data.py
```

Open pgAdmin at <http://localhost:8080> and sign in with the email and password
configured by `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` in
`docker-compose.yaml`. Register the database server using **Servers → Register
→ Server**:

1. In **General → Name**, enter any descriptive name.
2. In **Connection**, enter the PostgreSQL settings from Compose:

   | Setting | Value |
   | --- | --- |
   | Host name/address | `db` |
   | Port | `5432` |
   | Maintenance database | `ny_taxi` |
   | Username | `postgres` |
   | Password | `postgres` |

Run this query to count trips matching the date and distance criteria:

```sql
SELECT COUNT(*) AS trips_up_to_1_mile
FROM green_taxi_trips
WHERE lpep_pickup_datetime >= '2025-11-01'
  AND lpep_pickup_datetime < '2025-12-01'
  AND trip_distance <= 1.0;
```

- 7,853
- **8,007 — correct**
- 8,254
- 8,421

## Question 4. Longest trip for each day

Which pickup day had the longest trip distance? Consider only trips with
`trip_distance` less than 100 miles to exclude data errors. Use the pickup time
for the calculation.

```sql
SELECT DATE(lpep_pickup_datetime) AS pickup_day,
       trip_distance AS max_trip_distance
FROM green_taxi_trips
WHERE trip_distance < 100
ORDER BY trip_distance DESC
LIMIT 1;
```

- **2025-11-14 — result**
- 2025-11-20
- 2025-11-23
- 2025-11-25

## Question 5. Biggest pickup zone

Which pickup zone had the largest total `total_amount` across all trips on
November 18, 2025?

```sql
SELECT
    z."Zone" AS pickup_zone,
    SUM(g.total_amount) AS total_revenue
FROM green_taxi_trips AS g
JOIN taxi_zones AS z
    ON g."PULocationID" = z."LocationID"
WHERE DATE(g.lpep_pickup_datetime) = '2025-11-18'
GROUP BY z."Zone"
ORDER BY total_revenue DESC
LIMIT 1;
```

- **East Harlem North — result**
- East Harlem South
- Morningside Heights
- Forest Hills

## Question 6. Largest tip

For passengers picked up in the zone named "East Harlem North" during November
2025, which drop-off zone received the largest tip?

> **Note:** This question is about `tip_amount`, not `trip_distance`. Return the
> drop-off zone name, not its ID.

```sql
SELECT dropoff."Zone" AS drop_off_zone
FROM green_taxi_trips AS g
JOIN taxi_zones AS dropoff
    ON g."DOLocationID" = dropoff."LocationID"
JOIN taxi_zones AS pickup
    ON g."PULocationID" = pickup."LocationID"
WHERE pickup."Zone" = 'East Harlem North'
  AND g.lpep_pickup_datetime >= '2025-11-01'
  AND g.lpep_pickup_datetime < '2025-12-01'
ORDER BY g.tip_amount DESC
LIMIT 1;
```

- JFK Airport
- **Yorkville West — result**
- East Harlem North
- LaGuardia Airport

## Terraform

In this section, prepare the environment by creating resources in Google Cloud
Platform (GCP) with Terraform.

Install Terraform on your GCP VM, local machine, or GitHub Codespace. Copy the
files from the course repository's [`terraform`](terraform) directory to that
environment, then modify them as needed to create a GCP bucket and a BigQuery
dataset.

## Question 7. Terraform workflow

Which sequence describes the workflow for:

1. Downloading provider plugins and configuring the backend.
2. Generating the proposed changes and applying them automatically.
3. Removing all resources managed by Terraform.

Answers:

- `terraform import`, `terraform apply -y`, `terraform destroy`
- `terraform init`, `terraform plan -auto-apply`, `terraform rm`
- `terraform init`, `terraform run -auto-approve`, `terraform destroy`
- **`terraform init`, `terraform apply -auto-approve`, `terraform destroy` - result**
- `terraform import`, `terraform apply -y`, `terraform rm`

`terraform init` initializes the working directory and downloads providers.
`terraform apply -auto-approve` creates or updates resources without an
interactive approval prompt. `terraform destroy` removes the managed resources.

## Submitting the solutions

Submit your homework using the
[Module 1 homework form](https://courses.datatalks.club/de-zoomcamp-2026/homework/hw1).

## Learning in public

We encourage everyone to share what they learned. This is called "learning in
public".

### Why learn in public?

- **Accountability:** Sharing your progress creates commitment and motivation.
- **Feedback:** The community can offer useful suggestions and corrections.
- **Networking:** You'll connect with people who have similar interests.
- **Documentation:** Your posts become a learning journal you can revisit.
- **Opportunities:** Employers and clients may discover your work.

You can read more about the benefits in this
[article](https://aishippingblog.com/p/benefits-of-learning-in-public-and).

Don't worry about being perfect. Everyone starts somewhere, and people enjoy
following genuine learning journeys.

### Example post for LinkedIn

```text
🚀 Week 1 of Data Engineering Zoomcamp by @DataTalksClub complete!

Just finished Module 1 - Docker & Terraform. Learned how to:

✅ Containerize applications with Docker and Docker Compose
✅ Set up PostgreSQL databases and write SQL queries
✅ Build data pipelines to ingest NYC taxi data
✅ Provision cloud infrastructure with Terraform

Here's my homework solution: <LINK>

Following along with this amazing free course - who else is learning data engineering?

You can sign up here: https://github.com/DataTalksClub/data-engineering-zoomcamp/
```

### Example post for Twitter/X

```text
🐳 Module 1 of Data Engineering Zoomcamp done!

- Docker containers
- Postgres & SQL
- Terraform & GCP
- NYC taxi data pipeline

My solution: <LINK>

Free course by @DataTalksClub: https://github.com/DataTalksClub/data-engineering-zoomcamp/
```