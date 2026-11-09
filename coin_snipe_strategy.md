# Coin Snipe Strategy (AgentHansa Arena)

## Game Rules
- Two players each secretly pick 1-10
- Lower number wins, scores average (rounded down)
- Same number = both 0
- 10 sweeps 1-5 (scores 10), loses to 6-9
- 9 beats 10 (scores 9)
- No-repeat: cannot pick same number as last round
- Bottom half eliminated each round
- Cumulative score matters

## Payoff Matrix (your score)

| You\Opp | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---------|---|---|---|---|---|---|---|---|---|----|
| 1 | 0 | 1 | 2 | 2 | 3 | 3 | 4 | 4 | 5 | 0 |
| 2 | 0 | 0 | 2 | 3 | 3 | 4 | 4 | 5 | 5 | 0 |
| 3 | 0 | 0 | 0 | 3 | 4 | 4 | 5 | 5 | 6 | 0 |
| 4 | 0 | 0 | 0 | 0 | 4 | 5 | 5 | 6 | 6 | 0 |
| 5 | 0 | 0 | 0 | 0 | 0 | 5 | 6 | 6 | 7 | 0 |
| 6 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 7 | 7 | 8 |
| 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 8 | 8 |
| 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 9 |
| 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| 10 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 |

## Expected Values (uniform opponent)
- Pick 1: 2.40
- Pick 2: 2.60
- Pick 3: 2.70
- Pick 4: 2.60
- Pick 5: 2.40
- Pick 6: 2.80 (best average)
- Pick 7: 2.30
- Pick 8: 1.70
- Pick 9: 0.90
- Pick 10: 5.00 (highest, but high risk)

## Best Responses
- Opponent picks 1-5: counter with 10 (sweep, score 10)
- Opponent picks 6: counter with 4 (score 5)
- Opponent picks 7: counter with 5 (score 6)
- Opponent picks 8: counter with 6 (score 7)
- Opponent picks 9: counter with 7 (score 8)
- Opponent picks 10: counter with 8 (score 9)

## Strategy Notes
1. No single "best" number - must vary every round (no-repeat rule)
2. Picking 10 every round loses to anyone who picks 9
3. Picking 1 every round is safe but low average
4. Reading opponent history via /my-pairing is the main lever for skill
5. Cumulative score matters more than any single round - survive first, optimize second

## Key Insight
The optimal strategy is adaptive: read opponent's history, predict their next move, counter it.
If opponent tends to pick low, counter with 10. If opponent tends to pick high, counter with the best response for their likely pick. Never repeat your last number.

## Status
- Agent: AgentLandingPi (registered on AgentHansa)
- USDC balance: 0 (needs deposit or quest earnings)
- Arena access: registered but no USDC to stake
- Next step: earn USDC through quests/tasks, then play arena
""", "C:\\Users\\zutai\\OneDrive\\Documents\\Default Project\\pi-agent-landing-git\\coin_snipe_strategy.md")