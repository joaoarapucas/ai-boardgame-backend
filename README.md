# AI board game player backend
> this repo contains the code of an AI that plays a board game!

## About

this was a project for my college's 5th semester where our classroom competed in a board game using our own traditional AIs. The name of the board game is a secret not yet revealed by our teacher as an incentive for us to build the strategies ourselves. 

it was programmed in Python, and this player's strategy used Alpha-Beta Minimax with Iterative deepening depth-first. 

the bot has to make a move in 5 seconds or it loses the match automatically, so some improvements were required.

## Tech and details

the programming language was Python, with FastAPI to communicate with the game rules orchestrator API hosted by our professor. The API was hosted using Railway.

this bot's API has only two endpoints, which can be checked in the repo's about section:
- health: only used to check if the API is still running
- move: receives the board's current state, and makes a move based on it
Here's the completed strategy section and the new Limitations and Improvements section for your README:

## Strategy

The AI was programmed using the minimax adversarial search algorithm with some optimizations.

### TL:DR overview

At setup, the AI places the pieces around the middle ring of the board for better positioning and overall control of the board.

then, it separates its pieces into an offensive piece that will try to block the opponents moves, and a defensive piece that will try to climb and win the game. each piece has a different heuristic, although each one can still try to block/ climb up on their own.

the decisions are made by picking all possible moves, then simulating what would be the best for the player and for the enemy; then it picks the move that has the best branching result. The further it simulates moves, the smarter it is - although it costs more time.

### Opening Book

Before any tree search happens, the AI uses a technique borrowed from classical game AI called an **opening book**. In well-studied games like Chess, engines such as Stockfish ship with databases of thousands of pre-computed opening sequences, allowing the AI to skip expensive computation during the early game entirely and enter the midgame with a strong, well-known position.

This bot does something analogous: instead of running minimax on an empty or near-empty board (where the search space is wide and the heuristic signals are weak), it hardcodes a sensible opening strategy — placing pieces on the central ring of the 5×5 board. Cells like `(1,1)`, `(2,3)`, `(3,2)` etc. offer the best geometric coverage of the board, keeping both professors within reach of any square. This means the AI enters the midgame well-positioned without spending any of its 5-second clock thinking about it.

### Heuristics

Because in the bot strategy the two professors on each team have different roles (one offensive, one defensive), the AI uses a **role-aware heuristic** to evaluate board states.

Both professors share two baseline scoring components:
- **Height score** — being on a higher level cell is better, since level 3 is the win condition.
- **Mobility score** — having more legal moves available is better, as it avoids being cornered.

On top of that, each professor gets role-specific bonuses:

- **Offensive professors** (`CLARO`, `KARIN`) are rewarded for being adjacent to enemy pieces, as their goal is to interfere with and block the opponent's advancement. Distance penalties are applied the further they are from enemies.
- **Defensive professors** (`REY`, `BEATRIZ`) are rewarded for climbing — extra points are given for reaching level 1 and level 2, with a multiplier at level 2 since one more step is a win. They also receive proximity bonuses for being near high-level cells on the board, incentivising them to position for a future climb.

A shared **threat penalty** function scans the board for opponent professors that are already adjacent to a level-3 cell, applying a strong negative score to states where the opponent is one move from winning.

The final heuristic score for any board state is `my_score - opponent_score + threat_penalty`.

### Minimax with Alpha-Beta Pruning

The core search algorithm is **minimax**: the AI builds a game tree, alternating between the maximizing player (itself) and the minimizing player (the opponent), and picks the move that leads to the best guaranteed outcome assuming both sides play optimally.

![Minimax game tree](https://www.mygreatlearning.com/blog/wp-content/uploads/2020/05/Blog-8-5-2020-05-1024x567.jpg)

To make this feasible, it uses **alpha-beta pruning**. As the tree is explored, two values are maintained — `alpha` (the best the maximizer is guaranteed so far) and `beta` (the best the minimizer is guaranteed so far). Whenever `alpha >= beta`, the current branch can no longer influence the final decision and is cut off entirely. In practice, this can reduce the number of nodes evaluated from O(b^d) to roughly O(b^(d/2)), effectively doubling the searchable depth for the same computation budget.

Move ordering further improves pruning efficiency: before running the full minimax, moves are pre-sorted using a fast shallow heuristic (`move_score_quick`), so the most promising moves (e.g. climbs to level 3, upward steps) are explored first — making alpha-beta cuts happen earlier and more often.

Before the tree search even starts, two sanity checks short-circuit everything: if there is an immediate winning move available, take it; if the opponent has a winning move available, try to block it first.

### Iterative Deepening Search (IDS)

The game orchestrator enforces a **5-second time limit per move**, after which the bot forfeits automatically. A fixed-depth minimax risks either finishing too quickly (wasting thinking time) or overrunning the clock mid-search.

The solution is **iterative deepening**: the bot runs minimax at increasing depths (1, 2, 3... up to `MAX_DEPTH = 4`), always keeping track of the best move found so far. A `start` timestamp is threaded through every recursive call, and if `time.time() - start > TIME_LIMIT` (set to 4.3 seconds to give a safety margin), the search aborts and returns the best move found at the last completed depth. This way, the bot always has a valid move ready, and simply gets smarter the more time it has.

## Limitations and Improvements

### Weight Tuning via Genetic Algorithms

The heuristic weights (`HEIGHT_WEIGHT = 5.0`, `MOBILITY_WEIGHT = 1.0`, `BLOCK_WEIGHT = 1.5`, etc.) were set by hand through intuition and manual testing. While the bot currently wins 100% of its matches against a random-move AI, these values were not great against stronger opponents... :(

A natural next step would be to tune them automatically using a **genetic algorithm**. The idea is straightforward: generate a population of bots, each with a randomly initialised set of weight values; have them play round-robin tournaments against each other; select the individuals that won in the fewest turns (minimising turns is a stronger fitness signal than win rate alone, since it captures dominance rather than just survival); apply crossover and mutation to the survivors; and repeat for several generations. Over time, the population converges toward weight combinations that produce faster, more decisive wins.

## Resources

- [Minimax with Alpha-Beta Pruning in Python](https://stackabuse.com/minimax-and-alpha-beta-pruning-in-python/)
- [pi5-aux](https://github.com/guilhermeRey/pi5-aux/)
- [Chebyshev distance](https://en.wikipedia.org/wiki/Chebyshev_distance)
- [Algorithms](https://cs.stanford.edu/people/eroberts/courses/soco/projects/2003-04/intelligent-search/inter.html)
- Artificial Intelligence: A Modern Approach - Stuart J. Russell et al.
- Introduction to Algorithms, third edition - Thomas H. Cormen et al.
