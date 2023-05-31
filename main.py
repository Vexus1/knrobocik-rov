import numpy as np
import pygame
import sys
import os
import requests
from enum import Enum

pygame.init()

size = 600
screen = pygame.display.set_mode([size, size])
pygame.display.set_caption("Knrobocik")

bgCol = (0,255,255)
screen.fill(bgCol)
pygame.display.flip()

class GameAPI:
    @staticmethod
    def getGamefield():
        r = requests.get(url = "http://localhost:8000")
        data = r.json()
        return data["game_state"]
    
    @staticmethod
    def move(direct):
        if direct < 1 or direct > 4:
            return 0
    
        data = {'action':direct}
        p = requests.post(url = "http://localhost:8000", json = data)
        data = p.json()
        return data["result"]


class GameObject(Enum):
    MINE = 'o'
    NONE = ' '
    ROV = 'r'
    FLAG = 'x'
    OTHER = 'Z'
    STRAIGHT_HORIZONTAL = "H"
    STRAIGHT_VERTICAL = "V"
    TURN_LEFT_TO_TOP = "A"
    TURN_LEFT_TO_BOTTOM = "B"
    TURN_RIGHT_TO_TOP = "C"
    TURN_RIGHT_TO_BOTTOM = "D"
    LINE = None

class PathFinder:
    findedpath = [[0],[0]]
    maxPathFound = 1
    currentPathFound = 0
    seq = [
        [1,2,3,4],
        [1,4,2,3],
        [1,3,4,2],
        [1,2,4,3],
        [1,3,2,4],
        [1,4,3,2],
        [2,1,3,4],
        [2,4,1,3],
        [2,3,4,1],
        [2,1,4,3],
        [2,4,3,1],
        [2,3,1,4],
        [3,1,2,4],
        [3,4,1,2],
        [3,2,4,1],
        [3,1,4,2],
        [3,4,2,1],
        [3,2,1,4],
        [4,1,2,3],
        [4,3,1,2],
        [4,2,3,1],
        [4,1,3,2],
        [4,3,2,1],
        [4,2,1,3]
    ]

    def findPath(self, gamefield):
        self.findedpath = [[0],[0]]
        start = []
        exit = []
        for row in range(0, len(gamefield)):
            for col in range(0, len(gamefield[row])):
                if gamefield[row][col] == GameObject.ROV.value:
                    start = [row,col]
                elif gamefield[row][col] == GameObject.FLAG.value:
                    exit = [row,col]
        if (abs(start[0]-exit[0]) == 1 and start[1] == exit[1]) or (abs(start[1]-exit[1]) == 1 and start[0] == exit[0]):
            return [start,exit]
        for seq in self.seq:
            self.currentPathFound = 0
            self.checkNeighbourhood(gamefield, start[0],start[1], seq)
        return self.findedpath[0], self.findedpath[1]

    def checkNeighbourhood(self, gamefield, row, col, seq, pathX = np.array([]), pathY = np.array([])):
        if self.currentPathFound >= self.maxPathFound:
            return False
        if len(pathX) >= 20:
            return False

        top = 0
        bottom = len(gamefield) - 1
        right = len(gamefield[0]) - 1
        left = 0
        pathX = np.append(pathX, row)
        pathY = np.append(pathY, col)

        checkingField = gamefield[row][col]
        if checkingField == GameObject.FLAG.value:
            self.currentPathFound += 1
            if len(self.findedpath[0]) == 1 or len(self.findedpath[0]) > len(pathX):
                self.findedpath = [pathX, pathY]
            return False
        elif checkingField == GameObject.MINE.value:
            return False
        elif checkingField == GameObject.NONE.value or (checkingField == GameObject.ROV.value and len(pathX) <= 1):
            for seqNo in range(0,4):
                if seq[seqNo] == 1:
                    if col-1 >= left and not self.checkPath(pathX, pathY, row, col-1): 
                        self.checkNeighbourhood(gamefield, row, col-1, seq, pathX, pathY)
                if seq[seqNo] == 2:
                    if col+1 <= right and not self.checkPath(pathX, pathY, row, col+1): 
                        self.checkNeighbourhood(gamefield, row, col+1, seq, pathX, pathY)
                if seq[seqNo] == 3:
                    if row+1 <= bottom and not self.checkPath(pathX, pathY, row+1, col):
                        self.checkNeighbourhood(gamefield, row+1, col, seq, pathX, pathY)
                if seq[seqNo] == 4:
                    if row-1 >= top and not self.checkPath(pathX, pathY, row-1, col): 
                        self.checkNeighbourhood(gamefield, row-1, col, seq, pathX, pathY)
        return 

    def checkPath(self, pathX, pathY, checkingRow, checkingCol):
        for i in range(0, len(pathX)-1):
            if pathX[i] == checkingRow and pathY[i] == checkingCol:
                return True
        return False


class Game:
    __scale = size/10
    __path = os.getcwd() + "\\images\\"
    ROV = pygame.image.load(__path + "ROV.png").convert_alpha()
    mine = pygame.image.load(__path + "mine.png").convert_alpha()
    destination = pygame.image.load(__path + "destination.png").convert_alpha()
    line_hor = pygame.image.load(__path + "line.png").convert_alpha()
    curve_rtt = pygame.image.load(__path + "curve.png").convert_alpha()
    current_gamefield = []

    def __init__(self):
        self.ROV = pygame.transform.scale(self.ROV, (self.__scale,self.__scale))
        self.mine = pygame.transform.scale(self.mine, (self.__scale,self.__scale))
        self.destination = pygame.transform.scale(self.destination, (self.__scale,self.__scale))
        self.line_hor = pygame.transform.scale(self.line_hor, (self.__scale, self.__scale))
        self.line_ver = pygame.transform.rotate(self.line_hor, 90)
        self.curve_rtt = pygame.transform.scale(self.curve_rtt, (self.__scale, self.__scale))
        self.curve_ltt = pygame.transform.rotate(self.curve_rtt, 90)
        self.curve_ltb = pygame.transform.rotate(self.curve_rtt, 180)
        self.curve_rtb = pygame.transform.rotate(self.curve_rtt, 270)

    def draw(self):
        screen.fill(bgCol)
        row = 0
        col = 0
        self.current_gamefield = GameAPI.getGamefield()
        try:
            trace_row, trace_col = PathFinder().findPath(GameAPI.getGamefield())
            self.createTrace(trace_row, trace_col)
        except:
            print("Zostały tylko 2 pola")
        for i in self.current_gamefield:
            for j in i:
                self.putOnField(j,col,row)
                col += 1
            row += 1
            col = 0
        pygame.display.flip()

    def createTrace(self, trace_row, trace_col):
        for stepNo in range(1, len(trace_row)-1):
            pStep = stepNo - 1
            nStep = stepNo + 1
            direction = GameObject.NONE.value
            if trace_row[pStep] == trace_row[nStep]:
                direction = GameObject.STRAIGHT_HORIZONTAL.value
            if trace_col[pStep] == trace_col[nStep]:
                direction = GameObject.STRAIGHT_VERTICAL.value
            if (trace_row[pStep] == trace_row[nStep]+1 and trace_col[pStep] == trace_col[nStep]+1 and trace_row[stepNo] == trace_row[nStep])
            or (trace_row[pStep]+1 == trace_row[nStep] and trace_col[pStep]+1 == trace_col[nStep] and trace_col[stepNo] == trace_col[nStep]):
                direction = GameObject.TURN_LEFT_TO_BOTTOM.value
            if (trace_row[pStep]+1 == trace_row[nStep] and trace_col[pStep] == trace_col[nStep]+1 and trace_col[stepNo] == trace_col[nStep])
            or (trace_row[pStep] == trace_row[nStep]+1 and trace_col[pStep]+1 == trace_col[nStep] and trace_row[stepNo] == trace_row[nStep]): 
                direction = GameObject.TURN_RIGHT_TO_BOTTOM.value
            if (trace_row[pStep]+1 == trace_row[nStep] and trace_col[pStep] == trace_col[nStep]+1 and trace_row[stepNo] == trace_row[nStep])
            or (trace_row[pStep] == trace_row[nStep]+1 and trace_col[pStep]+1 == trace_col[nStep] and trace_col[stepNo] == trace_col[nStep]):
                direction = GameObject.TURN_LEFT_TO_TOP.value
            if (trace_row[pStep] == trace_row[nStep]+1 and trace_col[pStep] == trace_col[nStep]+1 and trace_col[stepNo] == trace_col[nStep])
            or (trace_row[pStep]+1 == trace_row[nStep] and trace_col[pStep]+1 == trace_col[nStep] and trace_row[stepNo] == trace_row[nStep]): 
                direction = GameObject.TURN_RIGHT_TO_TOP.value
            self.current_gamefield[int(trace_row[stepNo])][int(trace_col[stepNo])] = direction

    def putOnField(self, object, x, y):
        image = None
        if object == GameObject.MINE.value:
            image = self.mine
        elif object == GameObject.FLAG.value:
            image = self.destination
        elif object == GameObject.ROV.value:
            image = self.ROV 
        elif object == GameObject.STRAIGHT_HORIZONTAL.value:
            image = self.line_hor
        elif object == GameObject.STRAIGHT_VERTICAL.value:
            image = self.line_ver
        elif object == GameObject.TURN_LEFT_TO_BOTTOM.value:
            image = self.curve_ltb
        elif object == GameObject.TURN_LEFT_TO_TOP.value:
            image = self.curve_ltt
        elif object == GameObject.TURN_RIGHT_TO_BOTTOM.value:
            image = self.curve_rtb
        elif object == GameObject.TURN_RIGHT_TO_TOP.value:
            image = self.curve_rtt
        if image is None:
            return
        screen.blit(image, (x*self.__scale, y*self.__scale))

    def run(self):
        self.draw()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    moveType = 0
                    if event.key == pygame.K_LEFT:
                        moveType = 1
                    if event.key == pygame.K_UP:
                        moveType = 2
                    if event.key == pygame.K_RIGHT:
                        moveType = 3
                    if event.key == pygame.K_DOWN:
                        moveType = 4
                    if moveType != 0:
                        result = GameAPI.move(moveType)
                        self.draw()
                        if result == 3 or result == 0:
                            continue
                        elif result == 2:
                            print("przegrałeś")
                        elif result == 1:
                            print("wygrałeś")
                    

game = Game()
game.run()
