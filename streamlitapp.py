import streamlit as st
import cv2 
import mediapipe as mp 
import pyautogui 
import math 
from enum import IntEnum 
from ctypes import cast, POINTER 
from comtypes import CLSCTX_ALL 
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume 
from google.protobuf.json_format import MessageToDict 
import screen_brightness_control as sbcontrol
import os
from PIL import Image

pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils 
mp_hands = mp.solutions.hands 

class GestureController:  
    def __init__(this, hand_check):
        this.prev_sign = Gestures.PALM_NO_FINGER
        this.frame_count = 0
        this.ori__sign = Gestures.PALM_NO_FINGER
        this.result = None
        this.hand_check = hand_check
        this.finger = 0 
    
    #[8,5,0] shahadat wale ongale  [12,9,0] middle fingers [16,13,0] chote ongle barabr wale [20,17,0] chote onglae
    def set_finger(this): 
        if this.result == None: 
            return
        coordinates = [[8,5,0],[12,9,0],[16,13,0],[20,17,0]] 
        this.finger = 0
        this.finger = this.finger | 0 #thumb 
        for x, coordinate in enumerate(coordinates):             
            distance_of_c1 = this.get_distance(coordinate[:2]) 
            distance_of_c2 = this.get_distance(coordinate[1:])         
            try: 
                ratio = round(distance_of_c1/distance_of_c2,1) 
            except: 
                ratio = round(distance_of_c1/0.01,1) 
            this.finger = this.finger << 1
            if ratio > 0.5 : 
                this.finger = this.finger | 1


    def get_dist(this, coordinate): 
        dist = (this.result.landmark[coordinate[0]].x - this.result.landmark[coordinate[1]].x)**2
        dist += (this.result.landmark[coordinate[0]].y - this.result.landmark[coordinate[1]].y)**2
        dist = math.sqrt(dist) 
        return dist 
    
    
    def get_z_axis(this, coordinate): 
        return abs(this.result.landmark[coordinate[0]].z - this.result.landmark[coordinate[1]].z) 
    

    def updateresult(this, result): 
        this.result = result 

    
    def get_distance(this, coordinate): 
        sign = -1
        if this.result.landmark[coordinate[0]].y < this.result.landmark[coordinate[1]].y: 
            sign = 1
        distance = (this.result.landmark[coordinate[0]].x - this.result.landmark[coordinate[1]].x)**2
        distance += (this.result.landmark[coordinate[0]].y - this.result.landmark[coordinate[1]].y)**2
        distance = math.sqrt(distance) 
        return distance*sign 
    
    def Creation_of_gesture(this): 
        if this.result == None: 
            return Gestures.PALM_NO_FINGER
        curr_sign = Gestures.PALM_NO_FINGER
        if this.finger in [Gestures.LITTLE_FINGER]: 
            if this.hand_check == HandchecK.Left : 
                curr_sign = Gestures.P_LEFT
            else: 
                curr_sign = Gestures.P_RIGHT                  
        elif Gestures.F_2FINGER == this.finger : 
            coordinate = [[8,12],[5,9]] 
            distance_of_c1 = this.get_dist(coordinate[0]) 
            distance_of_c2 = this.get_dist(coordinate[1]) 
            ratio = distance_of_c1/distance_of_c2 
            if ratio > 1.7: 
                curr_sign = Gestures.MOUSE_MOVEMENT
            else: 
                if this.get_z_axis([8,12]) < 0.1: 
                    curr_sign = Gestures.DOUBLE_C
                else: 
                    curr_sign = Gestures.MIDDLE_F      
        else: 
            curr_sign = this.finger 
        
        if curr_sign == this.prev_sign: 
            this.frame_count += 1
        else: 
            this.frame_count = 0
        this.prev_sign = curr_sign 
        if this.frame_count > 4 : 
            this.ori__sign = curr_sign 
        return this.ori__sign

class HandchecK(IntEnum):  
    Left= 0   ;    Right = 1   

class HandController: 
    prev_hand = None; flag = False; grabflag = False; pinchmajorflag = False; pinchminorflag = False; 
    pinchstartxcoord = None; pinchstartycoord = None; grabflag = False; pinchdirectionflag = None; 
    flag = False; pinchlv = 0; framecount = 0; prev_hand = None; pinch_threshold = 0.3; prevpinchlv = 0
    
    def getpinchylv(result): 
        dist = round((HandController.pinchstartycoord - result.landmark[8].y)*10,1) 
        return dist 
    
    def scrollHorizontal(): 
        pyautogui.keyDown('shift') 
        pyautogui.keyDown('ctrl') 
        pyautogui.scroll(-120 if HandController.pinchlv > 0.0 else 120) 
        pyautogui.keyUp('ctrl') 
        pyautogui.keyUp('shift') 
    
    def brightnesschange(): 
        currentBrightnessLv = sbcontrol.get_brightness()/100.0
        currentBrightnessLv += HandController.pinchlv/50.0
        if currentBrightnessLv > 1.0: 
            currentBrightnessLv = 1.0
        elif currentBrightnessLv < 0.0: 
            currentBrightnessLv = 0.0    
        sbcontrol.fade_brightness(int(100*currentBrightnessLv) , start = sbcontrol.get_brightness()) 
   
    def getpinchxlv(result): 
        dist = round((result.landmark[8].x - HandController.pinchstartxcoord)*10,1) 
        return dist 

    def volumechange(): 
        devices = AudioUtilities.GetSpeakers() 
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None) 
        volume = cast(interface, POINTER(IAudioEndpointVolume)) 
        currentVolumeLv = volume.GetMasterVolumeLevelScalar() 
        currentVolumeLv += HandController.pinchlv/50.0
        if currentVolumeLv > 1.0: 
            currentVolumeLv = 1.0
        elif currentVolumeLv < 0.0: 
            currentVolumeLv = 0.0
        volume.SetMasterVolumeLevelScalar(currentVolume
