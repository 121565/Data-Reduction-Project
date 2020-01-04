try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle
import pygame
import numpy as np
import random as rand
import math
import time
pygame.init()

#The initiliazation
win = pygame.display.set_mode((500, 500))
pygame.display.set_caption("Checkerboard")
board = pygame.image.load('C:/Users/eelke/Desktop/Python/PyGame/Checkers/check.jpg')
menuscreen  = pygame.image.load('C:/Users/eelke/Desktop/Python/PyGame/Checkers/menuscreen.jpg')
Activeboard = np.zeros((8,8),'int')
Coordboard = [[x,y] for x in range(1,9) for y in range(1,9)]
isLightOn = False

''' On the Activeboard, a '1' stands for a white piece.
                  a '2' stands for a red piece

'''
clock = pygame.time.Clock()
turn = 'red'

def getnextmoves(move,turn,pieces,board):
    if nextmove(move,turn,pieces,board)==[]:
        return [move]

    tree=[]
    for child in nextmove(move,turn,pieces,board):
        branch = getnextmoves(child,turn,pieces,board)
        for stick in branch:
            tree.append(stick)
    return tree

def getnewboardfortraining(board,pieces):
    newboard = np.zeros((8,8),'int')
    for i in range(0,8):
        for j in range(0,8):
            newboard[i,j]=board[i,j]

    newwhitepieces=[]
    newredpieces=[]
    for wpiece in pieces[1]:
        newwhitepieces.append(piece(wpiece.position,wpiece.color,wpiece.isWhite,wpiece.king))
    for rpiece in pieces[0]:
        newredpieces.append(piece(rpiece.position,rpiece.color,rpiece.isWhite,rpiece.king))
    newpieces=[newredpieces,newwhitepieces]

    return newboard, newpieces

def getallposmoves(pieces,turn,board=Activeboard):
    allmoves = []
    allpospieceblocks= []
    if turn == 'white':
        i=1
        isWhite=True
    else:
        i=0
        isWhite=False
    for piece in pieces[i]:
        allposblocks = []
        allposblocks,isLightOn = check_options(piece.position[0],piece.position[1],piece.x-28,piece.y-27,turn,False,pieces,[],board)
        if allposblocks != []:
            for move in allposblocks:
                allpospieceblocks.append(move)
    noForcedmove=True
    for move in allpospieceblocks:
        if move.hitAPiece==True:
            noForcedmove=False
    for move in allpospieceblocks:
        if move.hitAPiece==True:
            branch = getnextmoves(move,turn,pieces,board)
            for stick in branch:
                newboard,piecesUpdate = getnewboardfortraining(board,pieces)
                newboard = boardupdate(newboard,piecesUpdate[i][stick.blockIndex].position,stick,isWhite)
                piecesUpdate[i][stick.blockIndex].update(stick.block)
                piecesUpdate[1-i]=remove_hit_pieces(piecesUpdate[1-i],stick,board,newboard)
                allmoves.append(treebranch(newboard,stick,piecesUpdate[0],piecesUpdate[1]))
        elif noForcedmove:
            newboard,piecesUpdate = getnewboardfortraining(board,pieces)
            newboard = boardupdate(newboard,piecesUpdate[i][move.blockIndex].position,move,isWhite)
            piecesUpdate[i][move.blockIndex].update(move.block)
            allmoves.append(treebranch(newboard,move,piecesUpdate[0],piecesUpdate[1]))
    return allmoves

def rewardfunc(redpieces,whitepieces):
    value=(len(redpieces)-len(whitepieces))
    for wpiece in whitepieces:
        if wpiece.king:
            value -= 1
    for rpiece in redpieces:
        if rpiece.king:
            value += 1
    return value

def makeGameTree(rpieces,wpieces,turn,Activeboard,depth):
    pieces=[rpieces,wpieces]
    gametree=treebranch(Activeboard,[],pieces[0],pieces[1])
    maxEval,treeIndex = minimax(gametree,depth,turn,gametree.pieces,gametree.boardstate,depth,-math.inf,math.inf)
    return treeIndex

def minimax(position,depth,turn,pieces,board,number,alpha,beta):
    if turn == 'white':
        i=1
    else:
        i=0
    if depth == 0 or not isTurn(pieces[i],turn,pieces,board) or pieces[0]==[] or pieces[1]==[]:
        return rewardfunc(position.redpieces,position.whitepieces)

    else:
        position.tree=getallposmoves(pieces,turn,board)

        if turn == 'red':
            if depth == number:
                maxEval = -math.inf
                for child in position.tree:
                    eval = minimax(child,depth-1,'white',child.pieces,child.boardstate,number,alpha,beta)
                    maxEval = max(maxEval,eval)

                    if eval == maxEval:
                        treeIndex = child
                return maxEval,treeIndex
            else:
                maxEval = -math.inf
                for child in position.tree:
                    eval = minimax(child,depth-1,'white',child.pieces,child.boardstate,number,alpha,beta)
                    maxEval = max(maxEval,eval)

                    alpha = max(alpha,eval)
                    if beta <= alpha:
                        break
                return maxEval

        if turn == 'white':
            if depth == number:
                maxEval = math.inf
                for child in position.tree:
                    eval = minimax(child,depth-1,'red',child.pieces,child.boardstate,number,alpha,beta)
                    maxEval = min(maxEval,eval)

                    if eval == maxEval:
                        treeIndex = child
                return maxEval,treeIndex
            else:
                maxEval = math.inf
                for child in position.tree:
                    eval = minimax(child,depth-1,'red',child.pieces,child.boardstate,number,alpha,beta)
                    maxEval = min(maxEval,eval)

                    beta = min(beta,eval)
                    if beta<= alpha:
                        break

                return maxEval


class treebranch(object):
    def __init__(self,boardstate,move,redpieces,whitepieces,t=0,n=0):
        self.move = move
        self.boardstate = boardstate
        self.redpieces = redpieces
        self.whitepieces = whitepieces
        self.pieces=[self.redpieces,self.whitepieces]
        self.t = t
        self.n = n
        self.tree = []

    def average(self):
        return self.t/self.n

# Let red maximise the score, White minimise
def rollout(branch,turn):
    if turn == 'white':
        i=1
    else:
        i=0
    while True:
        if branch.pieces[0]==[]:
            return rewardfunc(branch.redpieces,branch.whitepieces)
        elif branch.pieces[1]==[]:
            return rewardfunc(branch.redpieces,branch.whitepieces)
        elif not isTurn(branch.pieces[i],turn,branch.pieces,branch.boardstate):
            return rewardfunc(branch.redpieces,branch.whitepieces)
        allmoves = getallposmoves(branch.pieces,turn,branch.boardstate)
        randn = rand.randint(0, len(allmoves)-1)
        branch = allmoves[randn]
        if turn == 'white':
            i=0
            turn = 'red'
        else:
            i=1
            turn = 'white'

def expandTree(branch,turn):
    return getallposmoves(branch.pieces,turn,branch.boardstate)


def UCBI(branch,N):
    if branch.n != 0:
        return (branch.t/branch.n)+7*((math.log(N)/branch.n)**0.5)
    else:
        return math.inf

def treeTraversal(tree,N,turn):
    if turn == 'white':
        nextturn='red'
    else:
        nextturn = 'white'
    if tree.tree==[]:
        if tree.n == 0:
            v = rollout(tree,turn)
            tree.t += v
            tree.n += 1
            return v
        else:
            tree.tree = expandTree(tree,turn)
            if tree.tree != []:
                v = rollout(tree.tree[0],nextturn)
                tree.tree[0].t += v
                tree.tree[0].n += 1
                tree.t += v
                tree.n += 1
                return v
            else:
                v = rollout(tree,turn)
                tree.t += v
                tree.n += 1
                return v
    else:
        maxEval = - math.inf
        for branch in tree.tree:
            eval = UCBI(branch,N)
            if eval>maxEval:
                maxEval = eval
                maxBranch = branch
        v = treeTraversal(maxBranch,N,nextturn)
        maxBranch.t += v
        maxBranch.n += 1
        return v


def MCTS(gametree,iterations,turn):
    N=0 #Move counter
    for it in range(1,iterations+1):
        N+=1
        v = treeTraversal(gametree,N,turn)
    return gametree




class player(object):
    def __init__(self,x,y,height,width,color,coords,targets_hit = [],index = 25):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.block = coords
        self.color = color
        self.hits = targets_hit
        self.blockIndex = index
        if targets_hit == []:
            self.hitAPiece = False
        else:
            self.hitAPiece = True

    def draw(self,win):
        self.contour = (self.x,self.y,self.width,self.height)
        pygame.draw.rect(win,self.color, self.contour,2)

class piece(object):
    redpiece_num = 0
    whitepiece_num = 0
    def __init__(self,position,color,iswhite,isKing = False):
        self.position = position
        self.color = color
        self.isWhite = iswhite
        self.king = isKing
        self.x = 25+28+(self.position[1]-1)*56
        self.y = 30+27+(self.position[0]-1)*55
        if self.isWhite:
            self.num = piece.whitepiece_num
            piece.whitepiece_num += 1
        else:
            self.num = piece.redpiece_num
            piece.redpiece_num += 1

    def draw(self,win):
        self.coords = (25+28+(self.position[1]-1)*56,30+27+(self.position[0]-1)*55)
        pygame.draw.circle(win,self.color, self.coords, 20)
        if self.king == True:
            kingtext = font.render('K',1, (0,0,0))
            win.blit(kingtext, self.coords)

    def update(self,coords):
        self.position = coords
        if self.isWhite == True:
            if self.position in Coordboard[56:64]:
                self.king = True
        else:
            if self.position in Coordboard[0:8]:
                self.king = True
def boardupdate(board,init_pos,greenblock,isWhite):
    if isWhite:
        board[init_pos[0]-1,init_pos[1]-1] = 0
        board[greenblock.block[0]-1,greenblock.block[1]-1] = 1
    else:
        board[init_pos[0]-1,init_pos[1]-1] = 0
        board[greenblock.block[0]-1,greenblock.block[1]-1] = 2
    if greenblock.hits != []:
        for hit in greenblock.hits:
            board[hit[0]-1,hit[1]-1] = 0
    return board


def remove_hit_pieces(pieces,greenblock,board=Activeboard,newboard=[]):
    if greenblock.hits != []:
        for hit in greenblock.hits:
            for piece in pieces:
                if piece.position == hit:
                    id = pieces.index(piece)
            try:
                del(pieces[id])
            except:
                print("Something wrong is happening")
                print(greenblock.hits)
                print(hit)
                print(id)
                print(board)
                print(newboard)
    return pieces

def getpiece(coords,turn,pieces):
    if turn=='red':
        for piece in pieces[0]:
            if piece.position == coords:
                return piece
    if turn=='white':
        for piece in pieces[1]:
            if piece.position == coords:
                return piece


greenblocks = []
def check_options(p_posy,p_posx,player1x,player1y,turn,isLightOn,pieces,greenblocks = greenblocks,Activeboard = Activeboard):

    if turn == 'red':
        i =0
    elif turn == 'white':
        i=1
    if Activeboard[p_posy-1,p_posx-1] == 2-i:
        if turn == 'red':
            blockIndex = pieces[0].index(getpiece([p_posy,p_posx],turn,pieces))
        elif turn == 'white':
            blockIndex = pieces[1].index(getpiece([p_posy,p_posx],turn,pieces))

        if getpiece([p_posy,p_posx],turn,pieces).king==True:
            for side in range(0,2):
                b = 0
                while ([p_posy-1*(1-2*side)*(1+b),p_posx-1-b] in Coordboard):
                    if Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx-2-b]==0:
                        greenblocks.append(player(player1x-56-b*56,player1y-55*(1-2*side)*(1+b),55,55,(0,255,0),[p_posy-1*(1-2*side)*(1+b),p_posx-1-b],[],blockIndex))
                        isLightOn = True
                    elif Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx-2-b]==1+i:
                        if ([p_posy-(1-2*side)*(1+b)-(1-2*side),p_posx-2-b] in Coordboard):
                            if Activeboard[p_posy-(1-2*side)*(1+b)-(1-2*side)-1,p_posx-3-b]==0:
                                greenblocks.append(player(player1x-112-56*(b),player1y-110*(1-2*side)-55*(1-2*side)*b,55,55,(0,255,0),[p_posy-(1-2*side)*(1+b)-(1-2*side),p_posx-2-b],[[p_posy-(1-2*side)*(1+b),p_posx-2-b+1]],blockIndex))
                                isLightOn = True
                        b=20
                    elif Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx-2-b]==2-i:
                        b=20
                    b+=1
                b = 0
                while [p_posy-1*(1-2*side)*(1+b),p_posx+1+b] in Coordboard:
                    if Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx+b]==0:
                        greenblocks.append(player(player1x+56 +b*56,player1y-55*(1-2*side)*(1+b),55,55,(0,255,0),[p_posy-1*(1-2*side)*(1+b),p_posx+1+b],[],blockIndex))
                        isLightOn = True
                    elif Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx+b]==1+i:
                        if ([p_posy-(1-2*side)*(1+b)-(1-2*side),p_posx+2+b] in Coordboard):
                            if Activeboard[p_posy-(1-2*side)*(1+b)-(1-2*side)-1,p_posx+1+b]==0:
                                greenblocks.append(player(player1x+112+56*b,player1y-110*(1-2*side)-55*(1-2*side)*b,55,55,(0,255,0),[p_posy-(1-2*side)*(1+b)-(1-2*side),p_posx+2+b],[[p_posy-(1-2*side)*(1+b),p_posx+1+b]],blockIndex))
                                isLightOn = True
                        b=20
                    elif Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx+b]==2-i:
                        b=20
                    b+=1

        else:
            if ([p_posy-1+2*i,p_posx-1] in Coordboard):
                if Activeboard[p_posy-2+2*i,p_posx-2]==0:
                    greenblocks.append(player(player1x-56,player1y-55*(1-2*i),55,55,(0,255,0),[p_posy-1+2*i,p_posx-1],[],blockIndex))
                    isLightOn = True
                elif Activeboard[p_posy-2+2*i,p_posx-2]==1+i:
                    if ([p_posy-2+4*i,p_posx-2] in Coordboard):
                        if Activeboard[p_posy-3+4*i,p_posx-3]==0:
                            greenblocks.append(player(player1x-112,player1y-110*(1-2*i),55,55,(0,255,0),[p_posy-2+4*i,p_posx-2],[[p_posy-1+2*i,p_posx-1]],blockIndex))
                            isLightOn = True
            if [p_posy-1+2*i,p_posx+1] in Coordboard:
                if Activeboard[p_posy-2+2*i,p_posx]==0:
                    greenblocks.append(player(player1x+56,player1y-55*(1-2*i),55,55,(0,255,0),[p_posy-1+2*i,p_posx+1],[],blockIndex))
                    #         print('You can move this piece to the right')
                    isLightOn = True
                elif Activeboard[p_posy-2+2*i,p_posx]==1+i:
                    if ([p_posy-2+4*i,p_posx+2] in Coordboard):
                        if Activeboard[p_posy-3+4*i,p_posx+1]==0:
                            greenblocks.append(player(player1x+112,player1y-110*(1-2*i),55,55,(0,255,0),[p_posy-2+4*i,p_posx+2],[[p_posy-1+2*i,p_posx+1]],blockIndex))
                            isLightOn = True
    return greenblocks, isLightOn

#Check if there are any possible moves
def isTurn(pieces,turn,allpieces,board = Activeboard):
    allposblocks = []
    for piece in pieces:
        allposblocks,isLightOn = check_options(piece.position[0],piece.position[1],piece.x,piece.y,turn,False,allpieces,allposblocks,board)
    if allposblocks == []:
        return False
    else:
        return True


def nextmove(greenblock,turn,pieces,Activeboard = Activeboard):
    newblocks = []

    blockIndex = greenblock.blockIndex

    if turn == 'red':
        c =0
        piece = pieces[0][blockIndex]
    elif turn == 'white':
        c=1
        piece = pieces[1][blockIndex]

    p_posy = greenblock.block[0]
    p_posx = greenblock.block[1]
    player1x=greenblock.x
    player1y=greenblock.y


    if piece.king==True:
        for side in range(0,2):
            b = 0
            while ([p_posy-1*(1-2*side)*(1+b),p_posx-1-b] in Coordboard ):
                if Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx-2-b]==1+c and [p_posy-1*(1-2*side)*(1+b),p_posx-1-b] not in greenblock.hits:
                    if ([p_posy-(1-2*side)*(1+b)-(1-2*side),p_posx-2-b] in Coordboard):
                        if Activeboard[p_posy-(1-2*side)*(1+b)-(1-2*side)-1,p_posx-3-b]==0:
                            hits = greenblock.hits+[[p_posy-(1-2*side)*(1+b),p_posx-2-b+1]]
                            newblocks.append(player(player1x-112-56*(b),player1y-110*(1-2*side)-55*(1-2*side)*b,55,55,(0,255,0),[p_posy-(1-2*side)*(1+b)-(1-2*side),p_posx-2-b],hits,blockIndex))
                    b=20
                elif Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx-2-b]==2-c:
                    b=20
                b+=1
            b = 0
            while [p_posy-1*(1-2*side)*(1+b),p_posx+1+b] in Coordboard :
                if Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx+b]==1+c and [p_posy-1*(1-2*side)*(1+b),p_posx+1+b] not in greenblock.hits:
                    if ([p_posy-(1-2*side)*(1+b)-(1-2*side),p_posx+2+b] in Coordboard):
                        if Activeboard[p_posy-(1-2*side)*(1+b)-(1-2*side)-1,p_posx+1+b]==0:
                            hits = greenblock.hits+[[p_posy-(1-2*side)*(1+b),p_posx+1+b]]
                            newblocks.append(player(player1x+112+56*b,player1y-110*(1-2*side)-55*(1-2*side)*b,55,55,(0,255,0),[p_posy-(1-2*side)*(1+b)-(1-2*side),p_posx+2+b],hits,blockIndex))
                    b=20
                elif Activeboard[p_posy-1*(1-2*side)*(1+b)-1,p_posx+b]==2-c:
                    b=20
                b+=1

    else:
        for i in range(0,2):
            if ([p_posy-1+2*i,p_posx-1] in Coordboard) :
                if Activeboard[p_posy-2+2*i,p_posx-2]==1+c and [p_posy-1+2*i,p_posx-1] not in greenblock.hits:
                    if ([p_posy-2+4*i,p_posx-2] in Coordboard):
                        if Activeboard[p_posy-3+4*i,p_posx-3]==0:
                            hits = greenblock.hits+[[p_posy-1+2*i,p_posx-1]]
                            newblocks.append(player(player1x-112,player1y-110*(1-2*i),55,55,(0,255,0),[p_posy-2+4*i,p_posx-2],hits,blockIndex))
            if [p_posy-1+2*i,p_posx+1] in Coordboard :
                if Activeboard[p_posy-2+2*i,p_posx]==1+c and [p_posy-1+2*i,p_posx+1] not in greenblock.hits:
                    if ([p_posy-2+4*i,p_posx+2] in Coordboard):
                        if Activeboard[p_posy-3+4*i,p_posx+1]==0:
                            hits = greenblock.hits+[[p_posy-1+2*i,p_posx+1]]
                            newblocks.append(player(player1x+112,player1y-110*(1-2*i),55,55,(0,255,0),[p_posy-2+4*i,p_posx+2],hits,blockIndex))
    return newblocks


def redrawGameWindow():
    win.blit(board, (0,0))
    text = font.render('It is the {:s} players turn!'.format(turn),1, (255,255,255))
    win.blit(text,(190,10))

    for whitepiece in whitepieces:
        whitepiece.draw(win)
    for blackpiece in redpieces:
        blackpiece.draw(win)
    for blocks in greenblocks:
        blocks.draw(win)
    player1.draw(win)

    pygame.display.update()

#mainloop
font = pygame.font.SysFont('comicsans',30,True,False)
player1 = player(25,470-55,55,55,(255,0,0),[8,1])
whitepieces = []
redpieces = []
greenblocks = []
isPlayer2 = False
isPlayer = False

for x in range(1,4):
    odd = (x+1)%2
    for y in range(1,5):
        apiece = piece([x,odd+1+(y-1)*2],(255,255,255),True)
        whitepieces.append(apiece)
        Activeboard[x-1,odd+1+(y-1)*2-1] = 1
for x in range(6,9):
    odd = (x+1)%2
    for y in range(1,5):
        apiece = piece([x,odd+1+(y-1)*2],(255,0,0),False)
        redpieces.append(apiece)
        Activeboard[x-1,odd+1+(y-1)*2-1] = 2

another_turn = False
walkLoop = 0
greenLoop = 0
not_pressed = True
while not_pressed:
    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]:
        not_pressed = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            not_pressed = False
run = True

pieces = [redpieces,whitepieces]

'''
savedtree = treebranch(Activeboard,[],redpieces,whitepieces)
savedtree.tree= getallposmoves(pieces,turn,Activeboard)
MCTS(savedtree,1000,turn)
gametree=savedtree

with open('saved.tree', 'rb') as gametree_file:
    savedtree = pickle.load(gametree_file)
gametree = savedtree
'''
whitetime = 0
redtime = 0
avgredtime = 0
avgwhitetime = 0

while run:

    clock.tick(27)
    if walkLoop > 0:
        walkLoop += 1
    if walkLoop > 5:
        walkLoop = 0

    if greenLoop > 0:
        greenLoop += 1
    if greenLoop > 10:
        greenLoop = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    #The inputs:
    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT] and player1.x>35 and walkLoop == 0:
        player1.x -= 56
        walkLoop = 1
        player1.block[1]-=1
    if keys[pygame.K_UP] and player1.y>62.5 and walkLoop == 0:
        player1.y -= 55
        walkLoop = 1
        player1.block[0]-=1
    if keys[pygame.K_RIGHT] and player1.x<(410) and walkLoop == 0:
        player1.x += 56
        walkLoop = 1
        player1.block[1]+=1
    if keys[pygame.K_DOWN] and player1.y<410 and walkLoop == 0:
        player1.y += 55
        walkLoop = 1
        player1.block[0]+=1

    if greenLoop == 0:
    #if keys[pygame.K_SPACE] and greenLoop == 0:
        #makeGameTree(redpieces,whitepieces,turn,Activeboard)
        pieces = [redpieces,whitepieces]
        if turn == 'white' and not isPlayer2:
            greenLoop = 6

            #Recording how long it takes for the system to run
            start_time = time.time()

            '''
            greenblocks=[]
            tree=getallposmoves(pieces,turn,Activeboard)
            for branch in tree:
                greenblocks.append(branch.move)
            randn = rand.randint(0, len(greenblocks)-1)
            randommove = greenblocks[randn]
            bestmove = randommove
            '''

            bestmove = makeGameTree(redpieces,whitepieces,turn,Activeboard,6).move
            Activeboard = boardupdate(Activeboard,whitepieces[bestmove.blockIndex].position,bestmove,True)
            whitepieces[bestmove.blockIndex].update(bestmove.block)
            redpieces = remove_hit_pieces(redpieces,bestmove)
            turn = 'red'
            greenblocks = []

            comptime = (time.time() - start_time)
            avgwhitetime += comptime
            whitetime+= 1

            '''
            newgametree=0
            for branch in gametree.tree:
                if np.allclose(branch.boardstate,Activeboard):
                    newgametree=branch
            if newgametree==0:
                print('error')
            gametree = newgametree
            '''

        elif turn =='red' and not isPlayer:
            greenLoop = 6

            #Recording how long it takes for the system to run
            start_time = time.time()

            gametree = treebranch(Activeboard,[],redpieces,whitepieces)
            gametree.tree= getallposmoves(pieces,turn,Activeboard)
            MCTS(gametree,300,turn)
            MaxAv = -math.inf
            for branch in gametree.tree:
                Av = branch.n
                if Av > MaxAv:
                    MaxAv = Av
                    newgametree = branch
            print(MaxAv)
            gametree = newgametree
            bestmove = gametree.move

            #bestmove = makeGameTree(redpieces,whitepieces,turn,Activeboard,6).move
            randommove=bestmove

            Activeboard = boardupdate(Activeboard,redpieces[randommove.blockIndex].position,randommove,False)
            redpieces[randommove.blockIndex].update(randommove.block)
            whitepieces = remove_hit_pieces(whitepieces,randommove)
            turn = 'white'
            greenblocks = []

            comptime = (time.time() - start_time)
            avgredtime += comptime
            redtime+= 1

    if keys[pygame.K_SPACE] and greenLoop == 0:
        greenLoop = 1

        if turn == 'red' and isPlayer:
            if isLightOn == True:
                for greenblock in greenblocks:
                    if player1.block  == greenblock.block:
                        #Updating the board

                        another_turn = greenblock.hitAPiece

                        if another_turn == False:
                            Activeboard = boardupdate(Activeboard,redpieces[greenblock.blockIndex].position,greenblock,False)
                            redpieces[greenblock.blockIndex].update(greenblock.block)
                            whitepieces = remove_hit_pieces(whitepieces,greenblock)
                            turn = 'white'
                        else:
                            newmoves = nextmove(greenblock,turn,[redpieces,whitepieces])
                            if newmoves == []:
                                Activeboard = boardupdate(Activeboard,redpieces[greenblock.blockIndex].position,greenblock,False)
                                redpieces[greenblock.blockIndex].update(greenblock.block)
                                whitepieces = remove_hit_pieces(whitepieces,greenblock)
                                turn = 'white'
                                another_turn = False

                    if redpieces[greenblock.blockIndex].position in Coordboard[0:8]:
                        redpieces[greenblock.blockIndex].king = True
                if another_turn == False:
                    greenblocks = []
                    isLightOn = False
                else:
                    greenblocks = newmoves

            elif isLightOn == False:
                # See if the cursor is on a piece white can move
                greenblocks,isLightOn = check_options(player1.block[0],player1.block[1],player1.x,player1.y,turn,isLightOn,[redpieces,whitepieces],greenblocks)

        #White turn
        elif turn == 'white' and isPlayer2:
            if isLightOn == True:
                for greenblock in greenblocks:
                    if player1.block  == greenblock.block:
                        another_turn = greenblock.hitAPiece

                        if another_turn == False:
                            Activeboard = boardupdate(Activeboard,whitepieces[greenblock.blockIndex].position,greenblock,True)
                            whitepieces[greenblock.blockIndex].update(greenblock.block)
                            redpieces = remove_hit_pieces(redpieces,greenblock)
                            turn = 'red'
                        else:
                            newmoves = nextmove(greenblock,turn,[redpieces,whitepieces])
                            if newmoves == []:
                                Activeboard = boardupdate(Activeboard,whitepieces[greenblock.blockIndex].position,greenblock,True)
                                whitepieces[greenblock.blockIndex].update(greenblock.block)
                                redpieces = remove_hit_pieces(redpieces,greenblock)
                                turn = 'red'
                                another_turn = False
                    if whitepieces[greenblock.blockIndex].position in Coordboard[56:64]:
                        whitepieces[greenblock.blockIndex].king = True
                if another_turn == False:
                    greenblocks = []
                    isLightOn = False
                else:
                    greenblocks = newmoves

            elif isLightOn == False:
                # See if the cursor is on a piece white can move
                greenblocks,isLightOn = check_options(player1.block[0],player1.block[1],player1.x,player1.y,turn,isLightOn,[redpieces,whitepieces],greenblocks)



    redrawGameWindow()

    if redpieces == []:
        print("Congratulations for winning, white!")
        run = False
    elif whitepieces == []:
        print("Congratulations for winning, red!")
        run = False

    if turn == 'red':
        if not isTurn(redpieces,turn,[redpieces,whitepieces]):
            run = False
    if turn == 'white':
        if not isTurn(whitepieces,turn,[redpieces,whitepieces]):
            run = False
'''
with open('saved.tree', 'wb') as tree_file:
  pickle.dump(savedtree, tree_file)
'''

print('The average red time is:' , avgredtime/redtime)
print('The average white time is:', avgwhitetime/whitetime)
'''
Random:
0.0017581738923725329,0.0022711502878289473
red, with pruning:
3: 0.05537698268890381
4: 0.141553672877225
5: 0.4076504945755005
6: 0.7088731408119202,0.5651286401246723: 0.6370008904682962
7: 1.173029797417777, 1.7727345724900563, 1.6583598709106446: 1.534708080272826
8: 8.7664870262146, 4.469840049743652, 5.136863521907641: 6.124396865955298
red, without pruning:
3: 0.06582984924316407, 0.07512633800506592: 0.070478093624115
4: 0.2138981819152832, 0.2175208806991577: 0.21570953130722045
5: 1.2360222458839416, 0.6050410996312681, 0.9041809127444312: 0.9150814194198803
6: 4.770390367507934, 4.374216675758362: 4.572303521633148
7:
MCST:
200: 2.498007068634033,2.129901924133301, 2.842364881719862
300:  2.964074273904165, 3.556319841316768 , 3.9272443094561176  win: 3/4 ai strength: 3  0.019581768247816298 0.039681719195458195
300 : 3.138705940807567, 3.2421433771810224                     win: 2/4 ai strength: 4 0.06920909180360682 0.07967381477355957 0.12424707753317697
                                                             win: 1.5/4 strength: 5   0.29236109026016727    0.25577683448791505
                4.454690077088096                                win: 1.5/4  0.7215809363585252 0.7480172589421272 1.4140849330208518 1.0893983360259765
'''
print((2.964074273904165+ 3.556319841316768 + 3.9272443094561176+3.138705940807567+ 3.2421433771810224)/5)

print((0.019581768247816298 + 0.039681719195458195)/2)
print((0.06920909180360682 + 0.07967381477355957+ 0.12424707753317697)/3)
print((0.29236109026016727  +  0.25577683448791505))
print((0.7215809363585252+ 0.7480172589421272 +1.4140849330208518 +1.0893983360259765))
import matplotlib.pyplot as plt
x = [3,4,5,6]
y = [0.75,0.5,0.375,0.25]
plt.plot(x, y)

plt.xlabel('Depth of the tree')
plt.ylabel('Winrate of MCTS algorithm')
plt.title('Winrate for MCTS against Minimax')
plt.legend()
plt.show()

pygame.quit()
