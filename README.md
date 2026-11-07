# Course Scheduling Problem (CSP)

A Python-based course scheduling solver that generates academic schedules using **backtracking**, **constraint checking**, and **heuristic ordering**.

The project models course selection as a Constraint Satisfaction Problem (CSP), where student requests must be assigned to available academic terms while satisfying prerequisites, course availability, enrollment restrictions, and unit limits.

## Overview

Students may request multiple courses, with alternative options for each request. The solver attempts to select at most one course per request and assign it to a valid registered term.

The objective is to maximize the number of fulfilled requests while considering request weights as a secondary optimization criterion.

## Features

- **Backtracking Search:** Recursively explores possible course-to-term assignments.
- **Heuristic Ordering:** Processes requests with fewer available scheduling options first to reduce unnecessary search.
- **Prerequisite Checking:** Verifies that prerequisite courses have been completed or can be scheduled in an earlier term.
- **Term Availability:** Considers both student registration and course offering seasons.
- **Unit Constraints:** Enforces minimum and maximum unit limits for each academic term.
- **Alternative Course Options:** Allows each request to contain multiple course alternatives, selecting at most one.
- **Request Weights:** Supports weighted requests for secondary schedule optimization.
- **Additional Ordering Constraints:** Supports `after` clauses in course requests.

## How It Works

The solver follows these main steps:

1. **Load Input Data**
   - `courses.json` provides course information.
   - The student profile file provides registered terms, completed courses, unit limits, and course requests.

2. **Compute Available Slots**
   - For each requested course, the solver identifies registered terms in which the course is offered.
   - Optional request-specific term restrictions are also applied.

3. **Order Requests**
   - Requests are sorted by the number of possible course placements.
   - Requests with fewer options are considered first.

4. **Backtracking**
   - The solver explores course and term assignments recursively.
   - It checks course uniqueness, prerequisites, term availability, and maximum unit limits.
   - It also explores the possibility of skipping a request.

5. **Evaluate Schedules**
   - Completed candidate schedules are checked against minimum unit requirements.
   - The best solution is selected using a lexicographic score:
     1. Maximum number of fulfilled requests.
     2. Maximum total request weight.

6. **Generate Output**
   - The selected course-to-term assignments and total minimum units per term are printed.

## Input Format

The project uses two input files.

### 1. `courses.json`

Contains course definitions, including course IDs, names, unit ranges, prerequisites, and offered seasons.

Example:

```json
{
  "CS221": {
    "cid": "CS221",
    "name": "Artificial Intelligence",
    "minUnits": 3,
    "maxUnits": 4,
    "prereqs": ["CS109", "CS161"],
    "quarters": ["Aut", "Win"]
  }
}
```

### 2. Student Profile

The profile file defines the student's academic constraints and requests.

Example:

```text
minUnits 0
maxUnits 15
register Aut2015
register Win2016
taken CS106B
request CS229 or CS205A in Aut2015,Spr2016
request CS246 in Spr2016
```

Supported profile directives:

| Directive | Description |
|---|---|
| `minUnits` | Minimum units required in each registered term |
| `maxUnits` | Maximum units allowed in each registered term |
| `register` | Adds an available academic term |
| `taken` | Specifies a previously completed course |
| `request` | Defines a course request with optional alternatives and term restrictions |
| `weight` | Assigns a priority weight to a request |
| `after` | Specifies a course-ordering constraint |

## Usage

Make sure the following files are available in the project directory:

```text
course-scheduling-csp/
├── main.py
├── courses.json
└── profile2a.txt
```

Run the solver:

```bash
python main.py
```

The current implementation loads `courses.json` and `profile2a.txt` by default.

## Example Output

```text
Schedule:
  CS229 -> Aut2015
  CS246 -> Spr2016

Units per term:
  Aut2015: 3
  Win2016: 0
  Spr2016: 3
  Aut2016: 0
```

If no feasible schedule is found, the program prints:

```text
No feasible schedule found.
```

## Implementation Details

The solver is implemented in Python and uses:

- Recursive backtracking for exploring assignments.
- Sets and dictionaries for managing assignment state and course uniqueness.
- Precomputed available slots to avoid repeatedly calculating basic course availability.
- Heuristic request ordering to prioritize more constrained requests.
- Lexicographic scoring to compare candidate schedules.

The implementation relies only on Python's standard library:

- `json`
- `re`

## Current Limitations

- Unit calculations use each course's `minUnits`; course-level `maxUnits` are loaded but are not used when calculating term totals.
- The `after` constraint is not fully enforced when its referenced course has not yet been assigned. A final validation step would be needed to guarantee this ordering in every returned schedule.
- Prerequisite feasibility checks consider possible future assignments, but do not guarantee that every considered prerequisite will ultimately be selected.
- The search uses recursive backtracking and may become expensive as the number of requests and possible placements grows.

## Authors

- **Vahhab Balandomanesh**
- **Mohammadmahdi Kazemi**

Developed as an academic project focused on Constraint Satisfaction Problems, recursive search, and heuristic optimization.
