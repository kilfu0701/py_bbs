# -*- coding: cp950 -*-

""" 
  讀取UAO編碼表 
"""
def load_B2U_table():
    f = open('moz18-b2u-strict.txt' , 'r')
    data = f.readlines()
    uao_dict = {}
    for i in data[1:-1]:
        big5, unicode = str.split(i.strip(), ' ')
        uao_dict[big5] = unicode
    
    return uao_dict
    #print uao_dict['0xC765']