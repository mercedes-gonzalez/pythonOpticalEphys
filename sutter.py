"""
Created on Thu Mar 30 19:22:05 2017

@author: nzj
"""

import serial as srl


class Sutter_driver:  
    def __init__(self, port, baudrate,bytesize,stopbits,Ans = 0):
        self.obj = srl.Serial(port=port,baudrate=baudrate,bytesize=bytesize,stopbits=stopbits,timeout=3) 
        self.__Ans__ = Ans
        print((self.obj.portstr,'create successful'))

    def __del__( self ):  
        self.obj.close()
        print((self.obj.portstr,'close successful'))
     
    def WaitAnswer( self ):
        Cr = 0
        print ('waiting answer')
        if self.__Ans__:
            Cr = self.obj.read(1)
        return Cr
    
    def ChangeManipulator( self, Motor_str ):
        self.obj.write(Motor_str[:3])
        return self.WaitAnswer()
    
    def Calibration( self ):
        self.obj.write(b'N')
        return self.WaitAnswer()
    
    def CurrentPos( self ):
        self.obj.write(b'C')
        return self.obj.read(14)
    
    def Move2Pos( self, MotorPos_str ):
        self.obj.write(MotorPos_str[:14])
        return self.WaitAnswer()
    
    def Move2Home( self ):
        self.obj.write(b'H')
        return self.WaitAnswer()
    
    def Move2Work( self ):
        self.obj.write(b'Y')
        return self.WaitAnswer()
    
    def Interrupt( self ):
        self.obj.write(b'\x03')
        return self.WaitAnswer()
    

if __name__ == '__main__':
    # https://www.sutter.com/manuals/MPC-325_OpMan.pdf
    p = Sutter_driver(port='COM3',baudrate=128000,bytesize=8,stopbits=1)  

    pos = p.CurrentPos()
    print('pos = ', pos)
    posArray = bytearray(pos)
    driveNum = posArray[0]
    xByte = posArray[1:4]
    yByte = posArray[5:8]
    zByte = posArray[9:12]
    x_um_step = int.from_bytes(xByte,byteorder='little',signed=False)
    print('x (microsteps):', x_um_step)
    x_micron = x_um_step*.0625
    print('x (micron):', x_micron)

    print('done')
