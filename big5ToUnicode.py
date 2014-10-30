# -*- coding: cp950 -*-

""" 
  Ū��UAO�s�X�� 
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