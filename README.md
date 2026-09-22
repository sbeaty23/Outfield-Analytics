# Outfield Analytics

Outfield Analytics is a full-stack baseball analytics and machine-learning platform designed to combine current-season baseball data with historical datasets to provide team information, player statistics, schedules, trend analysis, projected depth charts, and game predictions.

The project is being built as a portfolio project to demonstrate practical experience with full-stack development, backend API design, relational databases, data engineering, machine learning, testing, containerization, and deployment.

## Project Goal

The goal of Outfield Analytics is to create an independent baseball analytics application that provides:

* Current team and player information
* Current-season statistics and standings
* Team rosters and coaching staff
* Team schedules
* Interactive statistical dashboards
* Historical performance analysis
* Projected depth charts based on player usage
* Machine-learning predictions for upcoming games
* Model evaluation and backtesting tools

The project is intended to go beyond simply displaying API data. The application will calculate its own advanced statistics, rolling trends, projections, and prediction features from the underlying data.

## Planned Features

### Team Overview

Each team will have an overview page containing information such as:

* Team record
* Winning percentage
* Division and league
* Division ranking
* Run differential
* Recent record
* Runs scored per game
* Runs allowed per game
* Offensive and pitching trends

Interactive charts will be used to visualize performance over time.

### Roster

The roster section will display the current team roster grouped by position.

Player information may include:

* Name
* Position
* Bats / Throws
* Current-season statistics

Players will also have individual profile pages containing season statistics and performance trends.

### Coaching Staff

The staff section will display current managers and coaches when that information is available from the selected data source.

### Statistics

The statistics section will provide sortable and filterable tables for:

* Batting
* Pitching
* Fielding

In addition to source statistics, Outfield Analytics will calculate additional metrics such as:

* AVG
* OBP
* SLG
* OPS
* ERA
* WHIP
* K/9
* BB/9
* HR/9
* Run differential
* Rolling team performance

### Projected Depth Chart

Outfield Analytics will generate its own projected depth chart based on player usage.

Factors may include:

* Recent starts
* Season starts
* Recent appearances
* Positional usage

The generated depth chart will be clearly labeled as a projection rather than an official team depth chart.

### Schedule

The schedule section will display current and upcoming games along with historical results.

Current-season schedule data will be requested only when needed and cached by the backend.

### Game Predictions

A machine-learning model will estimate the probability of each team winning an upcoming game.

Potential prediction features include:

* Season winning percentage
* Recent win percentage
* Run differential
* Offensive performance
* Pitching performance
* Recent team form
* Home-field advantage
* Rest days
* Starting pitching information

The initial model will use logistic regression as a baseline before being compared with other models such as:

* Random Forest
* Gradient Boosting
* XGBoost

### Model Lab

The Model Lab will provide information about how the prediction models perform.

Metrics may include:

* Accuracy
* ROC-AUC
* Brier Score
* Log Loss
* Calibration

Models will be trained and evaluated using chronological data splits to better simulate real-world prediction.

## Data Sources

Outfield Analytics uses a hybrid data strategy.

### Current-Season Data

Current-season information will be retrieved through MLB's publicly accessible statistics endpoints.

This data will only be used for narrow, non-bulk requests such as:

* Current rosters
* Current player statistics
* Current team statistics
* Standings
* Coaching staff
* Current and upcoming schedules

Requests will be made through the Outfield Analytics backend rather than directly from the browser.

Responses will be cached to reduce unnecessary requests.

### Historical Data

Historical baseball data used for analytics, machine-learning training, validation, and backtesting will primarily come from Retrosheet.

Historical datasets may include:

* Games
* Team statistics
* Player statistics
* Batting statistics
* Pitching statistics
* Rosters
* Historical schedules

Retrosheet data will be processed through a custom ETL pipeline and stored in PostgreSQL.

Required Retrosheet attribution will be included in the deployed application.

## Data Usage

Outfield Analytics is an independent, non-commercial portfolio project.

The project will not include:

* MLB logos
* Team logos
* Official player photographs
* Broadcast video or audio
* MLB articles or editorial content
* A live game feed
* Bulk redistribution of MLB data

The application is not affiliated with, endorsed by, sponsored by, or operated by Major League Baseball or any MLB club.

## Architecture

The planned application architecture is:

```text
                    Outfield Analytics
                           |
              +------------+------------+
              |                         |
           Next.js                   FastAPI
        React / TypeScript              |
                                        |
                         +--------------+--------------+
                         |              |              |
                       Redis        PostgreSQL      ML Layer
                         |              |              |
                         |              |        scikit-learn
                         |              |
                         +------+-------+
                                |
                     +----------+----------+
                     |                     |
                MLB Current            Retrosheet
                   Data              Historical Data
```

The frontend will never communicate directly with external baseball data providers.

Instead:

```text
Browser
   |
Next.js
   |
FastAPI
   |
Data Provider / Database
```

This keeps external data access, caching, normalization, and error handling centralized in the backend.

## Technology Stack

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Recharts

### Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic

### Database

* PostgreSQL

### Data Processing

* pandas
* NumPy

### Machine Learning

* scikit-learn
* XGBoost planned for later experimentation

### Infrastructure

* Docker
* Docker Compose
* Redis
* GitHub Actions

### Testing

* pytest
* Vitest
* React Testing Library

### Planned Deployment

* Vercel — frontend
* Railway or Render — backend
* PostgreSQL — application and analytics database
* Redis — caching

## Repository Structure

The planned repository structure is:

```text
Outfield-analytics/
|
├── frontend/
|   ├── app/
|   ├── components/
|   ├── hooks/
|   ├── services/
|   ├── types/
|   └── utils/
|
├── backend/
|   ├── app/
|   |   ├── api/
|   |   ├── providers/
|   |   ├── services/
|   |   ├── models/
|   |   ├── schemas/
|   |   ├── database/
|   |   └── main.py
|   └── tests/
|
├── ingestion/
|   ├── retrosheet/
|   └── transforms/
|
├── ml/
|   ├── features/
|   ├── training/
|   ├── evaluation/
|   ├── models/
|   └── notebooks/
|
├── docs/
|
├── .github/
|   └── workflows/
|
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Development Roadmap

The project will be developed in several phases.

### Phase 1 — Application Foundation

Set up the core application infrastructure.

Tasks include:

* Initialize the Next.js frontend
* Initialize the FastAPI backend
* Configure PostgreSQL
* Configure SQLAlchemy
* Configure Alembic database migrations
* Connect the frontend to the backend
* Connect the backend to PostgreSQL
* Add Docker and Docker Compose
* Add basic frontend and backend testing
* Add linting
* Add basic GitHub Actions CI
* Create project documentation

### Phase 2 — Current Baseball Data

Integrate current-season baseball information.

Planned work includes:

* Team data
* Team details
* Rosters
* Current statistics
* Schedules
* Standings
* Data normalization

### Phase 3 — Caching and Reliability

Add:

* Redis
* API caching
* Rate limiting
* Error handling
* Cached fallback data

### Phase 4 — Initial User Interface

Build:

* Team selector
* Overview
* Roster
* Stats
* Schedule

This will become the first publicly deployable version of the project.

### Phase 5 — Historical Data Pipeline

Create the Retrosheet ETL pipeline and historical PostgreSQL dataset.

### Phase 6 — Analytics

Add:

* Rolling statistics
* Performance trends
* Player pages
* Interactive charts
* Projected depth charts

### Phase 7 — Machine Learning

Build:

* Feature generation
* Training datasets
* Logistic regression baseline
* Prediction service

### Phase 8 — Model Evaluation

Add:

* Historical backtesting
* Chronological validation
* Calibration analysis
* Model comparisons
* Model Lab

### Phase 9 — Upcoming Game Predictions

Combine the trained historical model with current-season statistics to generate predictions for upcoming games.

### Phase 10 — Production Polish

Complete:

* Automated testing
* CI/CD
* Documentation
* Logging
* Production deployment
* Performance optimization

## Current Status

**Current Phase: Phase 1 — Application Foundation**

The project is currently focused on establishing the full-stack development environment before integrating baseball data.

Current work includes:

* [x] Project planning
* [x] Initial repository structure
* [x] `.gitignore` configuration
* [x] Environment variable template
* [x] Next.js frontend setup
* [x] FastAPI backend setup
* [ ] Frontend-to-backend communication
* [ ] PostgreSQL setup
* [ ] SQLAlchemy configuration
* [ ] Alembic migration setup
* [ ] Docker configuration
* [ ] Backend tests
* [ ] Frontend tests
* [ ] CI workflow

Phase 1 will be considered complete when the following request path works reliably:

```text
Browser
   |
Next.js
   |
FastAPI
   |
PostgreSQL
```

The entire local development environment should eventually be startable with:

```bash
docker compose up
```

## Phase 1 Target

The initial application will include a simple system-status page confirming that each major service is operational.

Example:

```text
Outfield Analytics

System Status

Frontend      Online
Backend       Connected
Database      Connected
```

Once this works consistently, development will move to Phase 2 and begin integrating current-season baseball data.

## Project Status

Outfield Analytics is currently under active development and is not yet ready for production use.

Features, architecture, database schemas, and prediction methodology may change as development continues.
