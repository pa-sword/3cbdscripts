'''
States that matter for this search:
Whos turn, phase, A health, B health, A cats (including ocelot), B changelings, B treasures, A tapped, B tapped, changeling is summonsick, 1:ocelot is alive 2:it's tapped
(bog is just two treasures)
'''

def startturn(state, stateString, dependencies):
    state[1] = "A" # Attack phase next
    state[9] = 0 #sickness for turn
    if state[0] == "A":
        #Untap ocelot, then cats
        if state[10] == 2:
            state[10] = 1
        state[7] = 0
        state[2] += 1
        setDependencies(stateString, newStateString(state), dependencies)
    if state[0] == "B":
        #Untap changelings
        state[8] = 0
        newState = state.copy()
        newState[3] -= 1
        newState[6] += 1
        setDependencies(stateString, newStateString(newState), dependencies)
        newState = state.copy()
        newState[3] -= 3
        newState[5] += 1
        newState[9] = 1
        setDependencies(stateString, newStateString(newState), dependencies)
        newState = state.copy()
        newState[3] -= 4
        newState[5] += 1
        newState[6] += 1
        newState[9] = 1
        setDependencies(stateString, newStateString(newState), dependencies)
    return

def attackphase(state, stateString, dependencies):
    state[1] = "P" # B for moving to blocks
    if state[0] == "B":
        for changelings in range(state[5]-state[9], -1, -1): #can't attack with the sick changeling
            newState = state.copy()
            state[7] = changelings
            setDependencies(stateString, newStateString(newState), dependencies)
    if state[0] == "A":
        for cats in range(state[4]-state[10], -1, -1):
            newState = state.copy()
            newState[7] = cats
            setDependencies(stateString, newStateString(newState), dependencies)
            if state[10] == 1:
                newState[10] = 2
                newState[7] = cats + 1
                setDependencies(stateString, newStateString(newState), dependencies)
    return

def beforedamage(state, stateString, dependencies):
    state[1] = "B"
    newState = state.copy()
    if state[0] == "B":
        if state[6] > 3:
            newState[6] -= 4
            newState[3] += int(float(3 * state[8]))
    if state[0] == "A" and state[7] > 0: #at least one attacker
        if state[6] > 3:
            newState[6] -= 4
            newState[3] += int(float(3 * (state[5]-state[8]))) #all untapped changelings can block
    setDependencies(stateString, newStateString(newState), dependencies)
    return

def blocksAndDamage(state, stateString, dependencies):
    state[1] = "E"
    if state[0] == "A":
        newState = state.copy()
        newState[7] -= min(state[5]-state[8],state[7]) #one block per untapped or attacker
        newState[3] -= newState[7]
        if newState[10] == 2:
            newState[2] += 1 #lifelink
            if state[5]-state[8] > 0:
                newState[10] = 0
        setDependencies(stateString, newStateString(newState), dependencies)
    if state[0] == "B":
        for dblblk in range(min(state[4]-state[4]%2,int(float(2*state[8]))),-1,-2): #blocking in pairs to remove changelings
          for chump in range(min(state[8]-dblblk//2, state[4]-dblblk),-1,-1): #can only block unblocked attackers, with untapped cats that are not paired
              newState = state.copy()
              newState[4] -= dblblk + chump
              newState[5] -= int(float(dblblk / 2))
              newState[2] -= int(float(3 * newState[5]))
              if newState[4] == 0: #using the ocelot as the last blocker
                  newState[2] += 1
                  newState[10] = 0
              if newState[2] == 0 and state[10] == 1: #If ocelot is relevant when forced to block
                  newState[2] = 1
                  newState[10] = 0
              setDependencies(stateString, newStateString(newState), dependencies)
    return

def endstep(state, stateString, dependencies):
    state[1] = "S" # For start of turn 
    newState = state.copy()
    if state[0] == "A" and state[10] > 0:
        newState[0] = "B"
        newState[4] += 1
        #if newState[4] + 2 > 9 #Ascend is not turn by turn
        #    newState[4] += 1
    elif state[0] == "A":
        newState[0] = "B"
    else:
        newState[0] = "A"
    setDependencies(stateString, newStateString(newState), dependencies)
    return

def playPhase(stateString, dependencies):
    state = readStateString(stateString)
    #print(stateString) #step by step debug info, especially using starting_string
    if state[2] < 1 or state[3] < 1:
        return []
    if state[1] == "S":
        startturn(state, newStateString(state), dependencies)
    elif state[1] == "A":
        attackphase(state, newStateString(state), dependencies)
    elif state[1] == "P":
        beforedamage(state, newStateString(state), dependencies)
    elif state[1] == "B":
        blocksAndDamage(state, newStateString(state), dependencies)
    elif state[1] == "E":
        endstep(state, newStateString(state), dependencies)
    return dependencies[stateString]

def extend_search(initialStateString, depth):
    dependencies = {initialStateString:[]}
    search_strings = [initialStateString]
    for iter in range(depth):
        new_search_strings = []
        for string in search_strings:
            new_search_strings.extend(playPhase(string, dependencies))
        new_search_strings = list(dict.fromkeys(new_search_strings))
        search_strings = new_search_strings
    return dependencies

def newStateString(state):
    stateString = f'{state[0]},{state[1]},{state[2]},{state[3]},{state[4]},{state[5]},\
{state[6]},{state[7]},{state[8]},{state[9]},{state[10]}' 
    """,{state[11]},\
{state[12]},{state[13]},{state[14]},{state[15]},{state[16]},{state[17]},\
{state[18]},{state[19]},{state[20]},{state[21]},{state[22]},{state[23]},\
{state[24]},{state[25]},{state[26]},{state[27]},{state[28]},{state[29]},{state[30]}'"""
    return stateString

def readStateString(stateString):
    state = stateString.split(",")
    state[2] = int(state[2])
    state[3] = int(state[3])
    state[4] = int(state[4])
    state[5] = int(state[5])
    state[6] = int(state[6])
    state[7] = int(state[7])
    state[8] = int(state[8])
    state[9] = int(state[9])
    state[10] = int(state[10])
    return state

def setDependencies(oldStateString, newStateString, dependencies):
    if newStateString not in dependencies:
        dependencies[newStateString] = []
    if newStateString not in dependencies[oldStateString]:
        dependencies[oldStateString].append(newStateString)
    return

if __name__ == "__main__":
    starting_string = "A,S,21,19,2,0,2,0,0,0,1"
    #starting_string = "A,S,20,20,1,0,2,0,0,0,1" #BMC goes first
    out = extend_search(starting_string, 50)
    print(out)
    '''
    f = open("out.txt", "w")
    f.write(str(out))
    f.close()
    '''