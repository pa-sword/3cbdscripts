# STATE
# Player A is elixir
# Player B is 2X walker
# Each game state will be stored as value of the format:
# {Who's turn}{turn phase}
# A{life total}{land status}{walker location (including tapped/untapped/sick)}{walker size}i{walker marked damage}
# ii{elixir location} <--7
# iiii{untapped thopter count}iiiii{tapped thopter count} <--9
# B{life total}{land status}{walker 1 location (including tapped/untapped}{walker 1 size}i{walker 1 marked damage}
# ii{walker 2 location (including tapped/untapped}{walker 2 size}iii{walker 2 marked damage}
# iiii{untapped thopter count}iiiii{tapped thopter count}

# {Who's turn}{turn phase}: Au, Aa, Ab, Am, Ba, Bb, Bm [A upkeep, A attackers, A blockers, A second main, B attackers, B blockers, B second main]
# {Life total}: big int
# {Land status}: U / T [untapped / tapped]
# {Walker location}: H / D / B / G / U / T [hand, Draw (top of library), B (bottom of library), Graveyard, Untapped (not sick), Tapped, Sick]
# {Walker Size}: big int
# {Elixir location}: H / D / B / U [Hand, Draw (top of library), B (bottom of library), Untapped]
# {All thopter counts}: big int

# When the program is running, state is a list which contains the state as individual pieces of information
# Dependencies is a dictionary with condensed versions of the state pointing to a list of other states.
# For example, if dependencies says: "Aa20TG0iHii20iii0" #TODO

#~~

# New model:
# Start game, choose start player
# Get starting state; Save that state.
# Make a seperate function for each phase, including untap and draw
# Especially a combat phase, which does not need its own state, but needs a very complex function
# Use the same state names from above
# Make a function that takes a start state and plays 1 phase, moving to a new start state. Iteration determines how it plays out that phase
# Also, in dependencies, keep track of: "A", "B", "T", or "U" for A wins, B wins, Tie, and Undecided, respectively.
# Depth now means the number of phases / decisions, not turns
# I will probably do a small depth to start so that pruning can be performed, then go deeper. (depth first search)
def startturn(state, stateString, dependencies): # Updated V2 TODO make sure that calling setDependencies liek this actully updates the dictionary.
    state[1] = "A" # Attack phase next
    if state[0] == "A": # TODO change turn at end step
        state[28] = "A" # A will attack next
        state[8] += state[9] #Untap thopters
        state[9] = 0 #^^
        if state[4] == "T":
            state[4] = "U"
        if state[4] == "G" and state[7] == "U": #If A should recur elixir+hangarback
            instantelixir(stateString, state, "A", dependencies)
            return # Returning early because the land is not untapped in this case
        else:
            state[3] = "U"
            if state[4] == "D":
                state[4] = "H"
            if state[7] == "D":
                state[7] = "H"
            if state[4] == "B":
                state[4] = "D"
            if state[7] == "B":
                state[7] = "D"
    if state[0] == "B":
        state[28] = "B" # B will attack next
        state[11] = "U" #Untap land
        state[18] += state[19] #Untap thopters
        state[19] = 0 #^^
        if state[12] == "T":
            state [12] = "U" #Untap Walker 1
        if state[15] == "T":
            state[15] = "U" #Untap Walker 2
    setDependencies(stateString, newStateString(state), dependencies)
    return

def attackphase(state, stateString, dependencies): # Updated V2
    state[1] = "B" # B for moving to blocks
    if state[0] == "B":
        state[28] = "A" # A will be able to block
        for walker1attack in range(state[12] == "U", -1, -1):
            for walker2attack in range(state[15] == "U", -1, -1):
                for thopterattack in range(state[18], -1, -1):
                    newState = state.copy()
                    if walker1attack:
                        newState[12] = "T"
                    if walker2attack:
                        newState[15] = "T"
                    newState[18] -= thopterattack
                    newState[19] += thopterattack
                    setDependencies(stateString, newStateString(newState), dependencies)
    if state[0] == "A":
        state[28] = "B" # B will block
        for walkerattack in range(state[4] == "U", -1, -1):
            for thopterattack in range(state[8], -1, -1):
                newState = state.copy()
                if walkerattack:
                    newState[4] = "T"
                newState[8] -= thopterattack
                newState[9] += thopterattack
                setDependencies(stateString, newStateString(newState), dependencies)
    return

def blocks(state, stateString, dependencies): #V2
    state[1] = "O" # Order blockers
    if state[0] == "B":
        state[28] = "B" # B gets to assign damage
        walker1attack = int(state[12] == "T") * state[13]
        walker2attack = int(state[15] == "T") * state[16]
        state[21] = walker1attack
        state[25] = walker2attack
        if walker1attack > 0:
            if state[8] >= 1: # A blocks *walker1attack* with 1 thopter
                newState = state.copy()
                newState[24] = 1
                for thopblock in range(min(state[19], state[8] - 1), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies)
            if state[8] >= walker1attack: # A kills walker with many thopters
                newState = state.copy()
                newState[24] = walker1attack
                for thopblock in range(min(state[19], state[8] - walker1attack), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies)
            if state[4] == "U": # A blocks walker with walker
                newState = state.copy()
                newState[22] = state[5]
                for thopblock in range(min(state[19], state[8]), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies) # Just walker
                if state[5] + state[8] + 1 >= walker1attack > 1 + state[5]:  #Block with walker and thopters, preparing to pump. Ensures that thopters are necessary
                    newState = state.copy() #A blocks with "weak" walker
                    newState[22] = state[5]
                    newState[24] = walker1attack - state[5] - 1
                    for thopblock in range(min(state[19], state[8] - newState[24]), -1, -1):
                        newState[20] = thopblock
                        setDependencies(stateString, newStateString(newState), dependencies)
                if state[5] + state[8] >= walker1attack > state[5]: # Same as above, but without pump required
                    newState = state.copy()
                    newState[22] = state[5]
                    newState[24] = walker1attack - state[5]
                    for thopblock in range(min(state[19], state[8] - newState[24]), -1, -1):
                        newState[20] = thopblock
                        setDependencies(stateString, newStateString(newState), dependencies) #TODO go to damage assignment
        if walker2attack > 0:
            if state[8] >= 1: # A blocks with 1 thopter
                newState = state.copy()
                newState[27] = 1
                for thopblock in range(min(state[19], state[8] - 1), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies)
            if state[8] >= walker2attack: # A kills walker with many thopters
                newState = state.copy()
                newState[27] = walker2attack
                for thopblock in range(min(state[19], state[8] - walker2attack), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies)
            if state[4] == "U": # A blocks walker with walker
                newState = state.copy()
                newState[26] = state[5]
                setDependencies(stateString, newStateString(newState), dependencies) # Just Walker
                if state[5] + state[8] + 1 >= walker2attack > 1 + state[5]:  #Block with walker and thopters, preparing to pump. Ensures that thopters are necessary
                    newState = state.copy() #A blocks with "weak" walker
                    newState[26] = state[5]
                    newState[27] = walker2attack - state[5] - 1
                    for thopblock in range(min(state[19], state[8] - newState[27]), -1, -1):
                        newState[20] = thopblock
                        setDependencies(stateString, newStateString(newState), dependencies) #TODO go to damage assignment
                if state[5] + state[8] >= walker2attack > state[5]: # Same as above, but without pump required
                    newState = state.copy()
                    newState[26] = state[5]
                    newState[27] = walker2attack - state[5]
                    for thopblock in range(min(state[19], state[8] - newState[27]), -1, -1):
                        newState[20] = thopblock
                        setDependencies(stateString, newStateString(newState), dependencies) #TODO go to damage assignment
        if walker1attack * walker2attack > 0: #Both attacking, no thopters
            if state[8] >= 2: #A blocks each with 1 thopter
                newState = state.copy()
                newState[24] = 1
                newState[27] = 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[8] > walker1attack: # A kills walker with many thopters, blocks other with 1
                newState = newState.copy()
                newState[24] = walker1attack
                newState[27] = 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[8] > walker2attack:
                newState = newState.copy()
                newState[24] = 1
                newState[27] = walker2attack
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[8] >= walker1attack + walker2attack: #A kills both walkers with thopters
                newState = newState.copy()
                newState[24] = walker1attack
                newState[27] = walker2attack
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[4] == "U":
                if state[5] + state[8] + 1 >= walker1attack > 1 + state[5]:  #Block with walker and thopters, preparing to pump. Ensures that thopters are necessary
                    newState = state.copy() #A blocks with "weak" walker
                    newState[22] = state[5]
                    newState[24] = walker1attack - state[5] - 1
                    if state[5] + state[8] + 1 > walker1attack: # Additionally, block with 1 thopter
                        newState[27] = 1
                        setDependencies(stateString, newStateString(newState), dependencies)
                    if state[5] + state[8] + 1 >= walker1attack + walker2attack and walker2attack > 1: # Additionally, kill other walker with thopters
                        newState[27] = walker2attack
                        setDependencies(stateString, newStateString(newState), dependencies)
                if state[5] + state[8] + 1 >= walker2attack > 1 + state[5]:  #Block with walker and thopters, preparing to pump. Ensures that thopters are necessary
                    newState = state.copy() #A blocks with "weak" walker
                    newState[26] = state[5]
                    newState[27] = walker2attack - state[5] - 1
                    if state[5] + state[8] + 1 > walker2attack: # Additionally, block with 1 thopter
                        newState[24] = 1
                    if state[5] + state[8] + 1 >= walker1attack + walker2attack and walker1attack > 1: # Additionally, kill other walker with thopters
                        newState[24] = walker1attack
                        setDependencies(stateString, newStateString(newState), dependencies)
                if state[5] + state[8] >= walker1attack > state[5]: # Same as above, but without pump required
                    newState = state.copy()
                    newState[22] = state[5]
                    newState[24] = walker1attack - state[5]
                    if state[5] + state[8] > walker1attack: # Additionally, block with 1 thopter
                        newState[27] = 1
                        setDependencies(stateString, newStateString(newState), dependencies)
                    if state[5] + state[8] >= walker1attack + walker2attack and walker2attack > 1: # Additionally, kill other walker with thopters
                        newState[27] = walker2attack
                        setDependencies(stateString, newStateString(newState), dependencies)
                if state[5] + state[8] >= walker2attack > state[5]:
                    newState = state.copy()
                    newState[26] = state[5]
                    newState[27] = walker2attack - state[5]
                    if state[5] + state[8] > walker2attack > state[5]: # Same as above, but without pump required # Additionally, block with 1 thopter
                        newState[24] = 1
                        setDependencies(stateString, newStateString(newState), dependencies)
                    if state[5] + state[8] >= walker1attack + walker2attack and walker1attack > 1: # Additionally, kill other walker with thopters
                        newState[24] = walker1attack
                        setDependencies(stateString, newStateString(newState), dependencies)
        if state[19] > 0 and walker1attack == 0 and walker2attack == 0: #flag; 18->19 attacks, not blocks
            newState = state.copy()
            for thopblock in range(min(state[19], state[8]), -1, -1):
                newState[20] = thopblock
                setDependencies(stateString, newStateString(newState), dependencies)
        #TODO Is this all of the cases? ^^
    if state[0] == "A":
        state[28] = "A" # Damage assignment FLAG; "T"
        walker1attack = int(state[4] == "T") * state[5]
        state[21] = walker1attack
        if walker1attack > 0:
            if state[18] >= 1: # B blocks with 1 thopter
                newState = state.copy()
                newState[24] = 1
                for thopblock in range(min(state[9], state[18] - 1), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies)
            if state[18] >= walker1attack: # B kills walker with many thopters
                newState = state.copy()
                newState[24] = walker1attack
                for thopblock in range(min(state[9], state[18] - walker1attack), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies)
            if state[12] == "U": # B blocks walker with walker 1
                newState = state.copy()
                newState[22] = state[13]
                for thopblock in range(min(state[9], state[18]), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies) # Just walker
                if state[13] + state[18] + 1 >= walker1attack > 1 + state[13]:  #Block with walker and thopters, preparing to pump. Ensures that thopters are necessary
                    newState = state.copy() #B blocks with "weak" walker
                    newState[22] = state[13]
                    newState[24] = walker1attack - state[13] - 1
                    for thopblock in range(min(state[9], state[18] - newState[24]), -1, -1):
                        newState[20] = thopblock
                        setDependencies(stateString, newStateString(newState), dependencies)
                if state[13] + state[18] >= walker1attack > state[13]: # Same as above, but without pump required
                    newState = state.copy()
                    newState[22] = state[13]
                    newState[24] = walker1attack - state[13]
                    for thopblock in range(min(state[9], state[18] - newState[24]), -1, -1):
                        newState[20] = thopblock
                        setDependencies(stateString, newStateString(newState), dependencies) #TODO go to damage assignment
            if state[15] == "U": # B blocks walker with walker 2
                newState = state.copy()
                newState[23] = state[16]
                for thopblock in range(min(state[9], state[18]), -1, -1):
                    newState[20] = thopblock
                    setDependencies(stateString, newStateString(newState), dependencies) # Just walker
                if state[16] + state[18] + 1 >= walker1attack > 1 + state[16]:  #Block with walker and thopters, preparing to pump. Ensures that thopters are necessary TODO only do this if land is untapped
                    newState = state.copy() #B blocks with "weak" walker
                    newState[23] = state[16]
                    newState[24] = walker1attack - state[16] - 1
                    for thopblock in range(min(state[9], state[18] - newState[24]), -1, -1):
                        newState[20] = thopblock
                        setDependencies(stateString, newStateString(newState), dependencies)
                if state[16] + state[18] >= walker1attack > state[16]: # Same as above, but without pump required
                    newState = state.copy()
                    newState[23] = state[16]
                    newState[24] = walker1attack - state[16]
                    for thopblock in range(min(state[9], state[18] - newState[24]), -1, -1):
                        newState[20] = thopblock
                        setDependencies(stateString, newStateString(newState), dependencies) #TODO go to damage assignment
            if state[12] == "U" and state[15] == "U": # double block
                newState = state.copy()
                newState[22] = state[13]
                newState[23] = state[16]
                setDependencies(stateString, newStateString(newState), dependencies)
        if state[9] > 0 and walker1attack == 0: #flag; 18->9 walker2 redundant
            newState = state.copy()
            for thopblock in range(min(state[9], state[18]), -1, -1):
                newState[20] = thopblock
                setDependencies(stateString, newStateString(newState), dependencies)
        #TODO Is this all of the cases? ^^ TODO this needs lots of testing
    #No blocks
    setDependencies(stateString, newStateString(state), dependencies)
    return

def orderBlockers(state, stateString, dependencies): #V2
    state[1] = "P" # P for pre-damage
    if state[0] == "A":
        state[28] = "B" # B gets to act next, before damage
        if state[22] * state[23] > 0:
            for order in range(1, 3):
                newState = state.copy() #1 first, 2 first
                newState[30] = order
                setDependencies(stateString, newStateString(newState), dependencies)
        elif state[22] * state[24] > 0 or state[23] * state[24] > 0:
            for order in range(3, 7): #Walker first, walker last, only kill if no pump, take out as many thopters as possible and still have choice on whether to kill it
                newState = state.copy()
                newState[30] = order
                setDependencies(stateString, newStateString(newState), dependencies)
        else:
            newState = state.copy()
            newState[30] = 0 # No choices
            setDependencies(stateString, newStateString(newState), dependencies)
    if state[0] == "B":
        state[28] = "A"
        if state[22] * state[24] > 0 or state[23] * state[27] > 0:
            for order in range(3, 7):
                newState = state.copy()
                newState[30] = order
                setDependencies(stateString, newStateString(newState), dependencies)
        else:
            newState = state.copy()
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)

def beforedamage(state, stateString, dependencies): # V2
    state[1] = "D" # D for assignment of damage
    if state[0] == "B":
        state[28] = "B"
        if state[3] == "U":
            if state[4] == "U":
                newState = state.copy()
                newState[4] = "T"
                newState[5] += 1
                if state[22] > 0: #FLAG; walkerblocking walker indicates size apparently
                    newState[22] += 1
                if state[26] > 0: #flag whay are both wbws incremented?
                    newState[26] += 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[7] == "U":
                newState = state.copy()
                if state[4] == "G":
                    state[1] = "L"
                    instantelixir(stateString, newState, "D", dependencies)
                else:
                    newState[2] += 5
                    newState[7] = "D"
                    setDependencies(stateString, newStateString(newState), dependencies)
    if state[0] == "A":
        state[28] = "B"
        if state[11] == "U":
            if state[12] == "U":
                newState = state.copy()
                newState[11] = "T"
                newState[12] = "T"
                newState[13] += 1
                if state[22] > 0:
                    newState[22] += 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[15] == "U":
                newState = state.copy()
                newState[11] = "T"
                newState[15] = "T"
                newState[16] += 1
                if state[23] > 0:
                    newState[23] += 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[15] == "U" and state[16] == "U":
                newState = state.copy()
                newState[11] = "T"
                newState[12] = "T"
                newState[13] += 1
                if state[22] > 0:
                    newState[22] += 1
                newState[15] = "T"
                newState[16] += 1
                if state[23] > 0:
                    newState[23] += 1
                setDependencies(stateString, newStateString(newState), dependencies)
    setDependencies(stateString, newStateString(state), dependencies)
    return

def damageAssignment(state, stateString, dependencies): # V2 TODO double check everything
    state[1] = "C" # C for resolve combat
    if state[0] == "A":
        state[28] = "A" # Post combat main phase
        if state[21] == 0: #TODO might not be perfect. check other blocking cases
            setDependencies(stateString, newStateString(state), dependencies)
            return
        if state[30] == 0:
            if state[21] > 0:
                state[6] = state[22] + state[23] + state[24]
                if state[22] > 0:
                    state[14] = state[21]
                if state[23] > 0:
                    state[17] = state[21]
                #if state[24] > 0:
                #    state[18] -= min(state[21], state[24]) #flag; assignment, not destruction
                state[30] = 0
                setDependencies(stateString, newStateString(state), dependencies)
        elif 3 > state[30] > 0:
            state[6] = state[22] + state[23] #flag newstate->state
            if state[21] >= state[22] + state[23]:
                newState = state.copy()
                newState[14] = state[13]
                newState[17] = state[21] - state[13]
                newState[30] = 0
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[30] == 1:
                newState = state.copy()
                newState[14] = state[21]
                newState[30] = 0
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[30] == 2:
                newState = state.copy()
                newState[17] = state[21]
                newState[30] = 0
                setDependencies(stateString, newStateString(newState), dependencies)
        elif state[30] == 3 or state[21] >= state[22] + state[23] + state[24] or state[30] == 6:
            newState = state.copy()
            if state[22] > 0:
                newState[14] = state[21]
                #newState[18] -= max(min(state[21] - state[13], state[24]), 0)
            elif state[23] > 0:
                newState[17] = state[21]
                #newState[18] -= max(min(state[21] - state[16], state[24]), 0)
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
        if state[30] == 4:
            # Only take out thopters
            newState = state.copy()
            #newState[18] -= min(state[21], state[24])
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
        if state[30] == 5:
            newState = state.copy()
            # # of thopters before walker = attacker size - walker size before pump
            numThopters = 0
            if state[22] > 0:
                numThopters = state[21] - state[22] + (state[12] == "T")
            if state[23] > 0:
                numThopters = state[21] - state[23] + (state[15] == "T")
            #newState[18] -= min(numThopters, state[24])
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
            if ((state[22] > 0 and state[12] == "U") or (state[23] > 0 and state[15] == "U")) and state[21] < state[22] + state[23] + state[24]:
                newState = state.copy()
                if state[22] > 0:
                    newState[14] = state[21]
                    #newState[18] -= max(min(state[21] - state[13], state[24]), 0)
                elif state[23] > 0:
                    newState[17] = state[21]
                    #newState[18] -= max(min(state[21] - state[16], state[24]), 0)
                newState[30] = 0
                setDependencies(stateString, newStateString(newState), dependencies)
        if state[30] == 6:
            newState = state.copy()
            # # of thopters before walker = attacker size - walker size after pump
            numThopters = 0
            if state[22] > 0:
                numThopters = state[21] - state[22] - (state[12] == "U")
            if state[23] > 0:
                numThopters = state[21] - state[23] - (state[15] == "U")
            #newState[18] -= min(numThopters, state[24])
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
    if state[0] == "B":
        if state[21] == 0 and state[25] == 0: #TODO might not be perfect. check other blocking cases
            setDependencies(stateString, newStateString(state), dependencies)
            return
        if state[30] == 0:
            if state[21] > 0:
                state[14] = state[22] + state[24]
                if state[22] > 0:
                    state[6] = state[21]
                #if state[24] > 0:
                #    state[8] -= min(state[21], state[24])
            if state[25] > 0: #walker 2 attacking
                state[17] = state[26] + state[27] #wb2damage = wbw2+tbw2
                if state[26] > 0: #A walker is blocking w2
                    #state[6] = state[21] #A walker damage is w1a? flag; wrong assignment
                    state[6] = min(state[26],state[25])
                #if state[27] > 0: #thopters blocking w2
                #    state[8] -= #min(state[25], state[27]) #A thopters die to w2a or ntb? flag
                #    state[8] -= max(state[25]-state[26],0) #should be assignment, not damage
                state[30] = 0
                setDependencies(stateString, newStateString(state), dependencies)
        elif state[30] == 3 or state[30] == 6:
            newState = state.copy()
            if state[22] > 0:
                newState[6] = state[21]
                #newState[8] -= max(min(state[21] - state[5], state[24]), 0)
            elif state[26] > 0:
                newState[6] = state[25]
                #newState[8] -= max(min(state[25] - state[5], state[27]), 0)
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
        if state[22] > 0 and state[21] >= state[22] + state[24]:
            newState = state.copy()
            newState[6] = state[5]
            #newState[8] -= state[24]
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
        if state[26] > 0 and state[25] > state[26] + state[27]:
            newState = state.copy()
            newState[6] = state[5]
            #newState[8] -= state[27]
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
        if state[30] == 4:
            # Only take out thopters
            newState = state.copy()
            numThopters = 0
            if state[22] > 0:
                numThopters = state[24]
                attack = state[21]
            if state[26] > 0:
                numThopters = state[27]
                attack = state[25]
            #newState[8] -= min(attack, numThopters)
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
        if state[30] == 5:
            newState = state.copy()
            # # of thopters before walker = attacker size - walker size before pump
            numThopters = 0
            if state[22] > 0:
                numThopters = state[21] - state[22] + (state[4] == "T")
                minThopters = state[24]
            if state[26] > 0:
                numThopters = state[25] - state[26] + (state[4] == "T")
                minThopters = state[27]
            #newState[8] -= min(numThopters, minThopters)
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
            if state[4] == "U" and ((state[22] > 0 and state[21] < state[22] + state[24]) or (state[26] > 0 and state[25] < state[26] + state[27])):
                newState = state.copy()
                if state[22] > 0:
                    newState[6] = state[21]
                    #newState[8] -= max(min(state[21] - state[5], state[24]), 0)
                elif state[23] > 0:
                    newState[6] = state[25]
                    #newState[8] -= max(min(state[25] - state[5], state[27]), 0)
                newState[30] = 0
                setDependencies(stateString, newStateString(newState), dependencies)
        if state[30] == 6:
            newState = state.copy()
            # # of thopters before walker = attacker size - walker size after pump
            numThopters = 0
            if state[22] > 0:
                numThopters = state[21] - state[22] - (state[4] == "U")
                minThopters = state[24]
            if state[26] > 0:
                numThopters = state[25] - state[26] - (state[4] == "U")
                minThopters = state[27]
            #newState[18] -= min(numThopters, state[27])
            newState[30] = 0
            setDependencies(stateString, newStateString(newState), dependencies)
    return

def resolvecombat(state, stateString, dependencies): #V2
    state[1] = "M" # M for moving to main phase
    if (state[4] == "U" or state[4] == "T") and state[6] >= state[5]:
        state[4] = "G"
        state[8] += state[5]
        state[5] = 0 #somebody flag, state[6]?
    if (state[12] == "U" or state[12] == "T") and state[14] >= state[13]:
        state[12] = "G"
        state[18] += state[13]
        state[13] = 0
        state[14] = 0
    if (state[15] == "U" or state[15] == "T") and state[17] >= state[16]:
        state[15] = "G"
        state[18] += state[16]
        state[16] = 0
        state[17] = 0
    if state[0] == "A":
        state[28] = "A"
        state[9] -= state[20] #A tapped thop - tbt
        state[18] -= state[20] #B untapped - tbt
        state[18] -= min(state[24],state[5]) #B untapped - ntbw1 FLAG; walkersize damage limit
        state[10] -= state[9] #B life - A tapped thop, state[9] = 0, elixir/tapping failed for some reason
        if state[21] > 0 and state[22] == 0 and state[23] == 0 and state[24] == 0: #walker1 unblocked
            state[10] -= state[5] #condition not met
    if state[0] == "B":
        state[28] = "B"
        state[19] -= state[20] #B tapped thop - tbt
        state[8] -= state[20] #A untapped thop - tbt
        #state[19] -= state[24] #B tapped thop - ntbw1 FLAG; 19?
        state[8] -= min(state[24],state[21])
        #state[19] -= state[27] #B tapped thop - ntbw2 FLAG; 19?
        state[8] -= min(state[27],state[25])
        state[2] -= state[19] #A life - B tapped thop
        if state[21] > 0 and state[22] == 0 and state[23] == 0 and state[24] == 0: #somebody FLAG, 23 is redundant
            state[2] -= state[13]
        if state[25] > 0 and state[26] == 0 and state[27] == 0:
            state[2] -= state[16]
    if state[2] <= 0:
        print("B wins")
        state[29] = "B"
        setDependencies(stateString, newStateString(state), dependencies)
        return # Return early because game over
    if state[10] <= 0:
        print("A wins")
        state[29] = "A"
        setDependencies(stateString, newStateString(state), dependencies)
        return # Return early because game over
    state[6] = 0
    state[14] = 0
    state[17] = 0
    state[20] = 0
    state[21] = 0
    state[22] = 0
    state[23] = 0
    state[24] = 0
    state[25] = 0
    state[26] = 0
    state[27] = 0
    state[30] = 0
    setDependencies(stateString, newStateString(state), dependencies)
    return

def secondmain(state, stateString, dependencies): # V2
    state[1] = "E" # E for end step
    if state[0] == "A":
        state[28] = "B"
        if state[3] == "U":
            if state[4] == "H":
                newState = state.copy()
                newState[3] = "T"
                newState[4] = "U"
                newState[5] = 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[7] == "H":
                newState = state.copy()
                newState[3] = "T"
                newState[7] = "U"
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[4] == "U" and state[7] == "H":
                newState = state.copy()
                newState[3] = "T"
                newState[4] = "T"
                newState[5] += 1
                newState[7] = "U"
                setDependencies(stateString, newStateString(newState), dependencies)
    if state[0] == "B":
        state[28] = "A"
        if state[11] == "U":
            if state[12] == "H":
                newState = state.copy()
                newState[11] = "T"
                newState[12] = "U"
                newState[13] = 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[15] == "H":
                newState = state.copy()
                state[11] = "T"
                state[15] = "U"
                state[16] = 1
                setDependencies(stateString, newStateString(newState), dependencies)
    setDependencies(stateString, newStateString(state), dependencies)
    return

def endstep(state, stateString, dependencies): # V2
    state[1] = "S" # For start of turn 
    if state[0] == "B":
        state[28] = "A"
        state[0] = "A" #FLAG; removed from conditionals
        if state[3] == "U":
            if state[4] == "U":
                newState = state.copy()
                newState[3] = "T"
                newState[4] = "T"
                newState[5] += 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[7] == "U":
                newState = state.copy()
                if newState[4] == "G": #flag changed to newstate
                    instantelixir(stateString, newState, "S", dependencies) #TODO edge case where B gets to make a decision
                else: #B's end step. A's land and elixir are untapped. A's walker is not in the grave.
                    newState[2] += 5 #flag; added line for elixir life
                    newState[7] = "D" #Elixir activation at B's EOT
                    setDependencies(stateString, newStateString(newState), dependencies)
    elif state[0] == "A":
        state[28] = "B"
        state[0] = "B"
        if state[11] == "U":
            if state[12] == "U":
                newState = state.copy()
                newState[11] = "T"
                newState[12] = "T"
                newState[13] += 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[15] == "U":
                newState = state.copy()
                newState[11] = "T"
                newState[15] = "T"
                newState[16] += 1
                setDependencies(stateString, newStateString(newState), dependencies)
            if state[12] == "U" and state[15] == "U":
                newState = state.copy()
                newState[11] = "T"
                newState[12] = "T"
                newState[13] += 1
                newState[15] = "T"
                newState[16] += 1
                setDependencies(stateString, newStateString(newState), dependencies)
    setDependencies(stateString, newStateString(state), dependencies)
    return

def instantelixir(stateString, state, nextPhase, dependencies): #V2 should work now
    state[1] = "L" #doing instant elixir is complicated
    state[28] = "B"
    newSS = newStateString(state)
    setDependencies(stateString, newSS, dependencies)
    state[2] += 5
    state[1] = nextPhase
    if nextPhase == "S" and state[0] == "A":
        state[28] = "B"
        state[0] = "B"
    elif nextPhase == "S" and state[0] == "B":
        state[28] = "A"
        state[0] = "A"
    newState = state.copy()
    newState[4] = "B"
    newState[7] = "D"
    setDependencies(newSS, newStateString(newState), dependencies)
    newState = state.copy()
    newState[4] = "D"
    newState[7] = "B"
    setDependencies(newSS, newStateString(newState), dependencies)
    return

def playPhase(stateString, dependencies):
    state = readStateString(stateString)
    if state[29] != "U":
        return []
    if state[1] == "S":
        startturn(state, newStateString(state), dependencies)
    elif state[1] == "A":
        attackphase(state, newStateString(state), dependencies)
    elif state[1] == "B":
        blocks(state, newStateString(state), dependencies)
    elif state[1] == "O":
        orderBlockers(state, newStateString(state), dependencies)
    elif state[1] == "P":
        beforedamage(state, newStateString(state), dependencies)
    elif state[1] == "D":
        damageAssignment(state, newStateString(state), dependencies)
    elif state[1] == "C":
        resolvecombat(state, newStateString(state), dependencies)
    elif state[1] == "M":
        secondmain(state, newStateString(state), dependencies)
    elif state[1] == "E":
        endstep(state, newStateString(state), dependencies)
    #TODO elixir
    return dependencies[stateString]

def extend_search(initialStateString, depth):
    dependencies = {initialStateString:[]}
    search_strings = [initialStateString]
    for iter in range(depth):
        new_search_strings = []
        for string in search_strings:
            new_search_strings.extend(playPhase(string, dependencies))
        new_search_strings = list(dict.fromkeys(new_search_strings)) #somebody *fixed
        search_strings = new_search_strings
    return dependencies

def reverse_search():
    pass #TODO

#~~

def newStateString(state):
    stateString = f'{state[0]},{state[1]},{state[2]},{state[3]},{state[4]},{state[5]},\
{state[6]},{state[7]},{state[8]},{state[9]},{state[10]},{state[11]},\
{state[12]},{state[13]},{state[14]},{state[15]},{state[16]},{state[17]},\
{state[18]},{state[19]},{state[20]},{state[21]},{state[22]},{state[23]},\
{state[24]},{state[25]},{state[26]},{state[27]},{state[28]},{state[29]},{state[30]}'
    return stateString

def readStateString(stateString):
    state = stateString.split(",")
    state[2] = int(state[2])
    state[5] = int(state[5])
    state[6] = int(state[6])
    state[8] = int(state[8])
    state[9] = int(state[9])
    state[10] = int(state[10])
    state[13] = int(state[13])
    state[14] = int(state[14])
    state[16] = int(state[16])
    state[17] = int(state[17])
    state[18] = int(state[18])
    state[19] = int(state[19])
    state[20] = int(state[20])
    state[21] = int(state[21])
    state[22] = int(state[22])
    state[23] = int(state[23])
    state[24] = int(state[24])
    state[25] = int(state[25])
    state[26] = int(state[26])
    state[27] = int(state[27])
    state[30] = int(state[30])
    return state

def setDependencies(oldStateString, newStateString, dependencies):
    '''
    if newStateString == "A,C,20,U,T,2,0,H,0,0,20,T,U,1,0,G,0,0,0,0,0,2,1,0,1,0,0,0,A,U,0":
        #A,M,20,U,T,2,0,H,0,0,20,T,U,1,0,G,0,0,-1,0,0,0,0,0,0,0,0,0,A,U,0 negative thops
        #A,C,20,U,T,2,1,H,0,0,20,T,U,1,0,G,0,0,0,0,0,2,0,0,1,0,0,0,A,U,0 untapped thop went missing
        #A,C,20,U,T,2,0,H,0,0,20,T,U,1,0,G,0,0,0,0,0,2,1,0,1,0,0,0,A,U,0 thop missing, damage missing
        print(oldStateString)
        print(newStateString)
    '''
    if newStateString not in dependencies:
        dependencies[newStateString] = []
    if newStateString not in dependencies[oldStateString]:
        dependencies[oldStateString].append(newStateString)
    return

if __name__ == "__main__":
    #Start state for A going first
    # print(readStateString("A,M,20,U,H,0,0,H,0,0,20,U,H,0,0,H,0,0,0,0,0,0,0,0,0,0,0,0,A,U,0"))
    # #Start state for B going first
    # print(readStateString("B,M,20,U,H,0,0,H,0,0,20,U,H,0,0,H,0,0,0,0,0,0,0,0,0,0,0,0,B,U,0"))

    # testA = "A,M,20,U,H,0,0,H,0,0,20,U,H,0,0,H,0,0,0,0,0,0,0,0,0,0,0,0,A,U,0"
    # testA1 = readStateString(testA)
    # print(testA1)
    # testB = newStateString(testA1)
    # print(testB)
    # print(testA == testB)
    #starting_string = "B,D,20,T,G,0,0,H,1,0,20,U,G,0,0,T,1,0,0,1,0,0,0,0,0,1,0,1,B,U,0" #[8]=-1 bugtest
    starting_string = "A,S,20,U,H,0,0,H,0,0,20,U,H,0,0,H,0,0,0,0,0,0,0,0,0,0,0,0,A,U,0"
    #dependencies = {starting_string: []}
    # playPhase(starting_string, dependencies)
    # print(dependencies)
    out = extend_search(starting_string, 50)
    #print(out)
#    '''
    f = open("out.txt", "w")
    f.write(str(out))
    f.close()
#    '''

#TODO each state actually needs to know what state is next, not what state just passed.
#This is because some abnormal states (instant elixir and damage assignment)

# Currently refactoring (V2)
# Each state tells you who's turn will it be in the next phase and what phase is next
# Also who is actionable next
