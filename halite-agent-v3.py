from kaggle_environments.envs.halite.helpers import *

# Directions a ship can move
directions = [ShipAction.NORTH, ShipAction.EAST, ShipAction.SOUTH, ShipAction.WEST]

# Will keep track of whether a ship is collecting halite or carrying cargo to a shipyard
ship_states = {}

#should make list for each ship with last moves, if last move was none for more than X turns, randmoize.

# Returns the commands we send to our ships and shipyards
def agent(obs, config):
    size = config.size
    board = Board(obs, config)
    me = board.current_player
    
    ################################
    # Imports and helper functions #
    ################################   

    import random

    # Takes a tuple with both values between (-size+1) to (size-1) and returns a vector with both values between -size/2 to size/2 by modding with size
    def vectorMod(x,y):
        if x<-size/2: 
            x= x+size
        if x>size/2: 
            x=x-size
        if y<-size/2: 
            y=y+size
        if y>size/2: 
            y=y-size
        return (x,y)

    # Returns best (not unique) direction to move from one position (fromPos) to another (toPos)
    # Example: If I'm at pos (0,0) and want to get to pos (0,20), I should choose South direction
    def getDirTo(fromPos, toPos):
        a= toPos[0]-fromPos[0]
        b= toPos[1]-fromPos[1]
        c=vectorMod(a,b)    
        ret1 = ShipAction.EAST
        ret2 = ShipAction.NORTH
        if c[0]>0: ret1 = ShipAction.EAST
        if c[0]<0: ret1 = ShipAction.WEST
        if c[1]>0: ret2 = ShipAction.NORTH
        if c[1]<0: ret2 = ShipAction.SOUTH
        if c[0]==0: return ret2
        if c[1]==0: return ret1
        if random.randint(0, 1)==0: return ret1  
        else: return ret2
        
        
    #doesn't consider optimal path positions now, e.g. (0,0) to (2,3): is it better to move north or east every step?

    #Returns distance between two positions
    def distFromTo(fromPos, toPos):
        a= toPos[0]-fromPos[0]
        b= toPos[1]-fromPos[1]
        c=vectorMod(a,b)
        return abs(c[0])+abs(c[1])

    #Returns a cell containing the maximum halite in a 2*radius+1 box around ship
    def maxHalitePos(ship,radius):
        x = ship.cell.position.x
        y = ship.cell.position.y
        max = ship.cell.halite
        ret = board[x,y]
        for i in range(x-radius,x+radius):
            for j in range(y-radius,y+radius):
                c=vectorMod(i,j)
                s=c[0]
                t=c[1]
                if c[0]<0: 
                    s=c[0]+size
                if c[1]<0: 
                    t=c[1]+size                    
                C = board[s,t]
                if max <= C.halite:
                    ret = C
                    max = C.halite
        return ret
    

    #Returns the closest ally shipyard to ship
    def closestAllyShipyard(ship):
        if len(me.shipyards)==0:
            return None
        ret=me.shipyards[0]
        minn=distFromTo(ship.position,ret.position)
        for shipyard in me.shipyards:
            dist=distFromTo(ship.position,shipyard.position)
            if dist<minn:
                minn=dist
                ret=shipyard
        return ret
    
    #Finds the closest ally ship to shipyard
    def closestAllyShip(shipyard):
        if len(me.ships)==0:
            return None
        ret=me.ships[0]
        minn=distFromTo(shipyard.position,ret.position)
        for ship in me.ships:
            dist=distFromTo(shipyard.position,ship.position)
            if dist<minn:
                minn=dist
                ret=ship
        return ret

    #Finds the closest ally collector ship to shipyard
    def closestcollectorShip(shipss,shipyard):
        if len(shipss)==0:
            return None
        ret=shipss[0]
        minn=distFromTo(shipyard.position,ret.position)
        for ship in shipss:
            dist=distFromTo(shipyard.position,ship.position)
            if dist<minn:
                minn=dist
                ret=ship
        return ret

    #Returns the closest enemy ship to ship
    def closestEnemyShip(ship):
        enemy_ships = [ship for ship in board.ships.values() if ship not in me.ships]
        if len(enemy_ships)==0:
            return None
        ret=enemy_ships[0]
        minn=distFromTo(ship.position,ret.position)
        for enemy_ship in enemy_ships:
            dist=distFromTo(ship.position,enemy_ship.position)
            if dist<minn:
                minn=dist
                ret=enemy_ship
        return ret

    #Returns the closest enemy ship to a shipyard
    def closestEnemyShiptoShipyard(shipyard):
        enemy_ships = [ship for ship in board.ships.values() if ship not in me.ships]
        if len(enemy_ships)==0:
            return None
        ret=enemy_ships[0]
        minn=distFromTo(shipyard.position,ret.position)
        for enemy_ship in enemy_ships:
            dist=distFromTo(shipyard.position,enemy_ship.position)
            if dist<minn:
                minn=dist
                ret=enemy_ship
        return ret

    #Returns the closest enemy shipyard to ship
    def closestEnemyShipyard(ship):
        enemy_shipyards = [shipyard for shipyard in board.shipyards.values() if shipyard not in me.shipyards]
        if len(enemy_shipyards)==0:
            return None
        ret=enemy_shipyards[0]
        minn=distFromTo(ship.position,ret.position)
        for enemy_shipyard in enemy_shipyards:
            dist=distFromTo(ship.position,enemy_shipyard.position)
            if dist<minn:
                minn=dist
                ret=enemy_shipyard
        return ret
    
    #Returns the opposite direction to direction
    def oppositeDir(direction):
        if direction:
            return directions[(directions.index(direction)+2)%4]

    #11111finds the enemy with one rank above you in terms of halite
    def opponentHalite(play):
        high1 = [p for p in board.opponents if p.halite>=play.halite]
        high2 = [p for p in board.opponents if p.halite<play.halite]
        high=[]
        if len(high1)>0:
            high=high1
        if len(high2)>0:
            high=high2
        if high==[]:
            return None
        enemy=high[0]
        for ene in high:
            if ene.halite < enemy.halite:
                ene=enemy
        return enemy

    #11111finds ship with low halite for one player (typically player is s me)
    def shipsslowhalite(shipss):
        lowhalitecounter=75
        return [s for s in shipss if s.halite<lowhalitecounter]
    
    #11111 finds ship with lowest halite not in above definition, or highest halite in above definition if former doesn't exist
    def shipsslowesthalite(play):
        if play.ships==[]:
            return None
        if len(play.ships)>0:
            abovelowhaliteships=[s for s in play.ships if s not in shipsslowhalite(play.ships)]
            if abovelowhaliteships==[]:
                shipcan=shipsslowhalite(play.ships)[0]
                for ss in shipcan:
                    if ss.halite>shipcan.halite:
                        ss=shipcan
                return shipcan
            if len(abovelowhaliteships)>0:
                shipcan=abovelowhaliteships[0]
                for s in abovelowhaliteships:
                    if s.halite<shipcan.halite:
                        s=shipcan
                return shipcan
    
    #11111find the closest enemy shipyard one rank above you relative to ships with low halite
    def closestenemyShipyardrelship(shipss):
        if shipss==None:
            return None
        ene1=opponentHalite(me)
        if ene1==None:
            return None
        if len(ene1.shipyards)==0:
            return None
        ene=ene1.shipyards[0]
        if shipsslowhalite(shipss)==[]:
            return None
        my=shipsslowhalite(shipss)[0]
        for x in opponentHalite(me).shipyards:
            for y in shipss:
                if distFromTo(ene.position,my.position) > distFromTo(x.position,y.position):
                    ene=x
                    my=y
        tup=(ene,my)
        return tup

        
    # Returns best direction in order to collect
    def collect(ship):
        # If halite at current location running low, 
        # move to the adjacent square containing the most halite
        
        minHaliteToFarm = 100
        if ship.cell.halite < minHaliteToFarm:
            neighbors = [ship.cell.north.halite, ship.cell.east.halite, 
                         ship.cell.south.halite, ship.cell.west.halite]
            best = max(range(len(neighbors)), key=neighbors.__getitem__)
            return directions[best]

    # Returns best direction in order to collect

    #### need to upgrade so that if ships last move was the opposite of current move it changes (prevent loop where ships goes back and forth) ####

    def newCollect(ship):
        # If halite at current location running low, 
        # move to the adjacent square containing the most halite
        
        radius = 4
        minHaliteToFarm = 100

        if ship.cell.halite < minHaliteToFarm:
            C = maxHalitePos(ship,radius)
            direction = getDirTo(ship.position, C.position)
           # if direction: 
                #if direction == directions[(directions.index(ship.next_action)+2)%4]:
                  #  return ship.next_action
               # else: 
                 #   return direction
            if direction: 
                return direction

    #Returns best direction in order to deposit cargo 
    def deposit(ship):
        # Move towards shipyard to deposit cargo
        if closestAllyShipyard(ship) == None:
            return None
        direction = getDirTo(ship.position,closestAllyShipyard(ship).position)
        if direction: 
            return direction
        
    def shouldShipConvert(ship):
        if len(me.shipyards) == 0:
            return False
        shipyardMinDist = 7
        maxShipyards = 3
        convertCostMultiplier = 5
        if distFromTo(ship.position,closestAllyShipyard(ship).position)>shipyardMinDist and (ship.halite+me.halite)>convertCostMultiplier*config.convertCost and len(me.shipyards)<maxShipyards:
            return True
        return False
    
#     def shouldShipyardSpawn(shipyard):
#         spawnCostMultiplier = 3
#         stepInterval = 10
#         shipsPerShipyard = 4
#         maxRoundToSpawn = 300
#         if me.halite>spawnCostMultiplier*config.spawnCost and board.step%stepInterval == 0 and len(me.ships)<shipsPerShipyard*len(me.shipyards) and board.step<maxRoundToSpawn:
#             return True
#         return False
    
    def shouldShipyardSpawn(shipyard):
        minHaliteToSpawn = 1050
        maxShips = 25
        maxRoundToSpawn = 300
        if me.halite>minHaliteToSpawn and len(me.ships)<maxShips and board.step<maxRoundToSpawn:
            return True
        return False
    
    #AGENT
    
    
    
    cur_ships = me.ships # list that holds all ships that are not converting next action
    cur_shipyards = me.shipyards # list that holds all shipyards that are not spawning next action
    protector = []
    ship_role = {}
        
    #Early Game
    
    collectorcount=10 #one more than the number of collectors

    if board.step>=1 and board.step<=collectorcount:
        cur_shipyards[0].next_action = ShipyardAction.SPAWN
        cur_shipyards.pop(0)     
        
    # If there are no ships, use first shipyard to spawn a ship.
    if len(me.ships) == 0 and len(me.shipyards) > 0 and board.step>collectorcount:
        cur_shipyards[0].next_action = ShipyardAction.SPAWN
        cur_shipyards.pop(0)

    # If there are no shipyards, convert first ship into shipyard.
    if len(me.shipyards) == 0 and len(me.ships) > 0:
        cur_ships[0].next_action = ShipAction.CONVERT
        cur_ships.pop(0)
    
    #Splitting all ships into collecting and attacking groups, and designating one to protect
    
    
    if len(me.shipyards)>0 and len(cur_ships)>0:
        for ship in cur_ships:
            #collecting_ships = [shipId for shipId in ship_states.keys() if ship_states[shipId]=="COLLECT"]
            ship_distShipyard = [ (ship, distFromTo(ship.position,me.shipyards[0].position) ) for ship in cur_ships] 
            ship_distShipyard.sort(key = lambda x: x[1])  
            collectorshipno=min(len(cur_ships)-1,collectorcount)
            ran=range(0,collectorshipno+1)
            for i in ran:
                if i==0:
                    ship_role[ship_distShipyard[i][0]]="PROTECT"
                    protector.append(ship_distShipyard[i][0])
                if i>0:
                    ship_role[ship_distShipyard[i][0]]="COLLECT"
    
    
    #Converting ships to shipyards
        
#     for ship in cur_ships:
        #if ship.next_action == None: 
            
#         if shouldShipConvert(ship):
#             ship.next_action = ShipAction.CONVERT
#             cur_ships.remove(ship)
#             continue  

        ### Part 1: Set the ship's state 

    for ship in cur_ships:

        #11111makes a zero halite ship protect the shipyard
        
#         if board.step>9 and shipsslowesthalite(me)!=None:
#             if ship==shipsslowesthalite(me) and ship.position!=me.shipyards[0].position:
#                 if distFromTo(ship.position,me.shipyards[0].position)>1:
#                     ship.next_action=oppositeDir(ship.next_action)
#                 if distFromTo(ship.position,me.shipyards[0].position)<=1 and closestEnemyShiptoShipyard(me.shipyards[0])!=None:
#                     threat=closestEnemyShiptoShipyard(me.shipyards[0])
#                     if distFromTo(threat.position,me.shipyards[0].position)>2:
#                         ship.next_action=newCollect(ship)
#                     if distFromTo(threat.position,me.shipyards[0].position)<=2:
#                         direction=getDirTo(ship.position,me.shipyards[0].position)
#                         ship.next_action=direction
                
        #11111attacking but doesn't avoid enemy ships yet
                
            if closestenemyShipyardrelship(me.ships)!= None:
                if ship == closestenemyShipyardrelship(me.ships)[1]:
                    shipyardkamikaze = closestenemyShipyardrelship(me.ships)[0]
                    direction = getDirTo(ship.position, shipyardkamikaze.position)
                    ship.next_action = direction

            if ship.halite <= 520: # If cargo is too low, collect halite
                ship.next_action = newCollect(ship)


            if ship.halite > 520: # If cargo gets very big, deposit halite
                ship.next_action = deposit(ship)


    #Spawning Ships
                
    for shipyard in cur_shipyards:       
        if shouldShipyardSpawn(shipyard):
            shipyard.next_action = ShipyardAction.SPAWN
            cur_shipyards.remove(shipyard)
            
                   
    #Randomization
    
    if random.randint(0, 8)==0:
        for ship in cur_ships:
            ship.next_action = directions[random.randint(0,3)]
            
            
    # Make sure that non COLLECT ships actually follow other strong oponnents instead of newCollect()
    
    
    #Code
            
    #Collision prevention or chase other player ships or shipyards
    
    enemyCollisionRadius = 2 # maybe 3?]
    enemyShipyardCollisionRadius = 4
    maxCargoToAllowDestroyingShipyard = 100
    
    for ship in me.ships: #using me.ships here because you want to stop CONVERT if it's worth to chase and to run away instead of CONVERTing if another ship is close
        #advanced: maybe you can still convert and then defend shipyard with by spawning a ship
        enemy = closestEnemyShip(ship)
        if enemy != None:
            if distFromTo(ship.position,enemy.position)<=enemyCollisionRadius:
                dir = getDirTo(ship.position,enemy.position)
                if ship.halite < enemy.halite:
                    ship.next_action = dir
                else:
                    ship.next_action = oppositeDir(dir)
        enemyShipyard = closestEnemyShipyard(ship)
        if enemyShipyard != None:
            if distFromTo(ship.position,enemyShipyard.position)<=enemyShipyardCollisionRadius and ship.halite < maxCargoToAllowDestroyingShipyard:
                ship.next_action = getDirTo(ship.position,enemyShipyard.position)

    #Making sure collecting ships are staying within the grid (note that only works with one shipyard)
    if len(me.shipyards)>0 and len(me.ships)>0:
        gridRadius = 5
        defendRadius = 1
        
        ships_futurePos = []
        for ship in cur_ships:      
            if ship in ship_role.keys():          
                if ship.next_action==None:               
                     ships_futurePos.append(ship.position)
                else:
                     ships_futurePos.append(ship.position.translate(ship.next_action.to_point(), size))

        for i in range(len(ships_futurePos)):
            if abs(me.shipyards[0].position.x-ships_futurePos[i].x)>gridRadius or abs(me.shipyards[0].position.y-ships_futurePos[i].y)>gridRadius:
                cur_ships[i].next_action=oppositeDir(cur_ships[i].next_action)


#this should be the "sit on shipyard" code; not sure if good so commented out
#         for ship in protector:
#             if ship.next_action!= None:
#                 cur = [s for s in cur_ships if s not in protector]
#                 if cur==[]:
#                     ship.next_action=newCollect(ship)
#                 if len(cur)>0:
#                     ret=cur[0]
#                     minn=distFromTo(me.shipyards[0].position,ret.position)
#                     for shipss in cur:
#                         dist=distFromTo(me.shipyards[0].position,shipss.position)
#                         if dist<minn:
#                             minn=dist
#                             ret=shipss
#                     if distFromTo(ret.next_action.position,me.shipyards[0].position)>1:
#                         if ship.position==me.shipyards[0].position:
#                             if me.shipyards[0].next_action!=None:
#                                 ship.next_action=newCollect(ship)
#                             if me.shipyards[0].next_action==None:
#                                 ship.next_action=None
#                         if ship.position!=me.shipyards[0].position:
#                             ship.next_action=deposit(ship)
#                     if distFromTo(ret.next_action.position,me.shipyards[0].position)<=1:
#                         ship.next_action=newCollect(ship)
        
        #defender ship
        for ship in protector:
            if ship.next_action!= None:
                coord=ship.position.translate(ship.next_action.to_point(), size)
                if abs(me.shipyards[0].position.x-coord.x)>defendRadius+1 or abs(me.shipyards[0].position.y-coord.y)>defendRadius+1:
                    ship.next_action=oppositeDir(ship.next_action) #makes sure is in defending radius, need to code collection within radius
                enemy_ships = [ship for ship in board.ships.values() if ship not in me.ships]
                if enemy_ships!=[]:
                    threat=closestEnemyShiptoShipyard(me.shipyards[0])
                    if distFromTo(threat.position,me.shipyards[0].position)>0 and distFromTo(threat.position,me.shipyards[0].position)<=defendRadius+2:
                        if ship.position==me.shipyards[0].position:
                            direction=getDirTo(ship.position,threat.position)
                            ship.next_action=direction #if enemy ship nearby, try to kill it if protector on shipyard
                        else:
                            ship.next_action=deposit(ship) #otherwise deposit
            
    #Shipyard spawn collision check
    
    shipyard_collision = [] # list containing all next action position for ships in cur_ships
    for ship in cur_ships:
            if ship.next_action==None:               
                shipyard_collision.append(ship.position)
            else:
                shipyard_collision.append(ship.position.translate(ship.next_action.to_point(), size))
    shipyard_pos = [shipyard.position for shipyard in me.shipyards if shipyard not in cur_shipyards] # list containing all shipyards spawning ships in next action
    for shipyardPos in shipyard_pos:
        for i in range(len(shipyard_collision)):
            ship=cur_ships[i]
            if shipyardPos==shipyard_collision[i]:
                if ship.next_action==None:
                    ship.next_action = newCollect(ship)
                else:
                    ship.next_action=None  
                    
    #Collision prevention with self only
    #board_cpy=board.next()
    
    i=0
    while(True):
        collision_test = []
        for ship in cur_ships:
            if ship.next_action==None:               
                collision_test.append(ship.position)
            else:
                collision_test.append(ship.position.translate(ship.next_action.to_point(), size))
        duplicates = [index for index, pos in enumerate(collision_test) if pos in (collision_test[:index] + collision_test[(index+1):])]
        if len(duplicates)==0 or i==100:
            break
        for index in duplicates:
            ship=cur_ships[index]
            if ship.next_action != None:
                if i<10:
                    ship.next_action = oppositeDir(ship.next_action)
                else:
                    ship.next_action = directions[(directions.index(ship.next_action)+1+2*(i%2))%4]
        i+=1
            
            
    
    
    
    #Prevent ships from crashing early game
    
                                       
    return me.next_actions