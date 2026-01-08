# MentorMatch
![MentorMatch logo](app/static/assets/mentormatch.png)

## What is MentorMatch?
MentorMatch is a service designed to pair mentors to mentees. Each user can create a customizable profile,
allowing them to select as many preferred partners as they like. When all of the profiles are complete, MentorMatch will
generate a mapping that maximizes the happiness of all parties involved.

## How does MentorMatch work?
The designation of mentors and mentees naturally forms the structure of a [bipartite graph](https://en.wikipedia.org/wiki/Bipartite_graph).
We generate our assignments via solving a max-weight bipartite matching problem. Our weights are defined as follows:

- Both partners listed each other as preferred (2 points)
- Exactly one partner listed another as preferred  (1 point)
- Neither partner listed each other as preferred (0 points)

Matching can then be formalized as follows. Let $n$ be the number of mentors and mentees and $P_n$ the set of $n \times n$ permutation matrices. We solve:
```math
\underset{P \in P_n}{\arg\max} \sum_{i=1}^n \sum_{j=1}^n w_{ij} \cdot P_{ij}
```
where the nonzero terms of $P$ correspond to the ids of the matched mentors and mentees. This is solved efficiently via the user of SciPy's `linear_sum_assignment` function.

## How can I see my matching?
Once all preference data is accumulated, the full matching can be generated via the "Getting Started" page. It can also be downloaded as a separate CSV file,
which lists the mentor-mentee pairs as well as the matching score.

## Build Instructions
The cloud deployment of MentorMatch can be found [here](https://big-little-match-f65608553a2f.herokuapp.com/home). For users wishing to build locally:
```bash
git clone https://github.com/colbyendres/MentorMatch
cd MentorMatch
pip install -r requirements.txt
```
MentorMatch uses Postegres for the database and requires the `SECRET_KEY` variable for maintaining sessions. The app is configured to set these config variable from an `.env` file in the top-level directory
```bash
echo "DATABASE_URL=your-postgres-url" >> .env
echo "SECRET_KEY=your-secret-key" >> .env
```
With the configuration variables set, MentorMatch can be run with `flask run`.
