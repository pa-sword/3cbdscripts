# Ocelot Pride VS Black Market

## Requirements
The code for this brute forcer is in rust. It requires the [cargo and rustc](https://doc.rust-lang.org/cargo/getting-started/installation.html) utilities to compile and run.


## Running

Please be advised that the script can run for prolonged periods.
The test run for this (that completed) went on for 2 days.

That said, to build and run the project:
```cargo run```
From the project root.

## Input/Output
the program takes a boardstate as input, and a list of valid decisions to make for the player
with the initiative

the programm outputs "OP" if the ocelot player can force a win given the input
the program outputs "BMC" if the black market player can force a win given the input

## Heuristics and compromise
This brute forcer makes a number of assumptions, mainly for complexity reasons
Some blocking lines for the Ocelot Player are ignored;
- lines combining trading and chumping are not calculated
- lines trading with ocelot are not calculated

This is acceptable because 
- these lines seems weak in a vacuum (even though they might be locally correct)
- I did an amount of hand calcs for the matchup that comfort me in the idea that its not necessary
- As far as I'm aware, all ignored lines of decision are decision made by the ocelot player, which means that any "Ocelot Player win" outcome

Secondly, the program will only ever go to turn 15.
    if the game goes this long, it is considered a win for BMC
    this is partly to be congruent with the above consideration (i.e make the "OP win" result definitive).
    it's also to not get an overflow in memory.

## Logic
The program implements a state machine, where at any point all possible transitions are explored
until a winning one is found for the decision-making player (at wich point other options are culled)
or none are found (meaning at this decision point, opponent has forced a win for themselves)


## Possible improvement
It's highly probable this program can be optimized.
The easy optimization may have to do with reordering the option vectors to make sure forced wins are reached faster. (i.e favoring attacks over passing for both players), and more generally avoid lines that require both players to pass.

It seems possible to memorize the outcome of specific boardstates at start of turn, and cull
the ones that are in strictly worse (or striclty equivalent) position for the deciding player. this would organically cut lines that rely on both players repeateadly passing, without needing the hard 15 turn limit. The issue with that is I have no idea of the space bound for valid combination of state values.
it's probably in the order of factorial of the number of individual variables in the state.
But it might be more, and I would rather not have the program overflow until I know the upper bound for it.

