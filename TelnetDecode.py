# -*- coding: cp950 -*-

""" 
  for decode Telnet codes 
"""    
def telnet_decode(nnn):
    position = 0
    text_out = ''
    SEG_LEN = (0x7E-0x40 + 1) + (0xFE - 0xA1 + 1)


    for i in range(0, len(nnn), 2 ):
        #print 'pos:', position

        if (position+2) == len(nnn):
            cch1 = nnn[position] + nnn[position+1]
            cch2 = '00'
            #cch2 = nnn[position+2] + nnn[position+3]
        elif (position+4) > len(nnn):
            break
        else:
            cch1 = nnn[position] + nnn[position+1]
            cch2 = nnn[position+2] + nnn[position+3]   
        
        #print cch1, cch2
        ch = cch1 + cch2
        
        # 轉換成int運算
        ch1 = int(cch1, 16)
        ch2 = int(cch2, 16)
        #print ch1, ch2
        
        
        index = -1
        
        if ch1 >= 0x81 and ch1 <= 0xFE and ch2 >= 0x40 and ch2 <= 0xFE:
            '''
            if ch1 >= 0x81 and ch1 <= 0xA0: # 0x8140 - 0xA0FE
                if ch2 <= 0x7E: # ch2 should be within 0x40 ~ 0x7E or 0x A1 ~ 0xFE
                    index = (ch1 - 0x81) * SEG_LEN + (ch2 - 0x40)
                    index *= 2
                    
                elif ch2 >= 0xA1:
                    index = (ch1 - 0x81) * SEG_LEN + (0x7E-0x40 + 1) + (ch2 - 0xA1)
                    index *= 2
                    
            elif ch1 >= 0xC6 and ch1 <= 0xC8: # 0xC640 - 0xC8FE
                # ch2 should be within 0x40 ~ 0x7E or 0x A1 ~ 0xFE
                if (ch2 <= 0x7E):
                    index = ((ch1 - 0xC6) + (0xA0 - 0x81 + 1)) * SEG_LEN + (ch2 - 0x40)
                    index *= 2
                    
                elif ch2 >= 0xA1:
                    index = ((ch1 - 0xC6) + (0xA0 - 0x81 + 1)) * SEG_LEN + (0x7E-0x40 + 1) + (ch2 - 0xA1)
                    index *= 2
                    
            elif ch1 >= 0xFA and ch1 <= 0xFE: # 0xFA40 - 0xFEFE
                if (ch2 <= 0x7E): # ch2 should be within 0x40 ~ 0x7E or 0x A1 ~ 0xFE
                    index = ((ch1 - 0xFA) + (0xA0 - 0x81 + 1) + (0xC8 - 0xC6 + 1)) * SEG_LEN + (ch2 - 0x40)
                    index *= 2
                    
                elif ch2 >= 0xA1:
                    index = ((ch1 - 0xFA) + (0xA0 - 0x81 + 1) + (0xC8 - 0xC6 + 1)) * SEG_LEN + (0x7E-0x40 + 1) + (ch2 - 0xA1)
                    index *= 2
            if index >= 0:
                print ch1, ch2, index
                pass # big52Ucs2
            '''
            #-- 不需要B2U decode table --#
            if 0:
                pass
            else:
                # multibyte
                text_out = text_out + (ch).decode('hex')
                #print '==> multi-byte:', (ch).decode('hex'), ch
                position = position + 4
        
        else:# ascii
            if ch1 >= 0x81:
                #cch1 = '3f'
                text_out = text_out + (cch1).decode('hex')
                #print '==> ascii(OT):', (cch1).decode('hex')
                position = position + 2
            else:
                text_out = text_out + (cch1).decode('hex')
                position = position + 2
                #print 'ascii:', text_out

    return text_out
'''
ddd = '11/08 jeanvanjohn  R: [\xb3t\xb3\xf8] \xbc@\xb3\xf5 \xc5]\xaak\xa4\xd6\xa4k\xc7e\xc7P\xc6\xf1\xa1\xb8\xc7\xda\xc7\xaa\xc7\xa7 \xa9l\xb0\xca (\xc2\xbd\xa1K\x1b[K'
print telnet_decode(ddd.encode('hex')).decode('cp950').encode('big5')
print telnet_decode('\xF7\x34'.encode('hex') )

print telnet_decode('\x8d\xdb'.encode('hex'))
print telnet_decode('\x95\xB5'.encode('hex'))
f = open('B2U', 'rb')
data = f.read()
# 10進位
print ord(data[6446])
print ord(data[6446+1])
# > \x42\x57
print telnet_decode('\xa1\x42'.encode('hex'))
'''
