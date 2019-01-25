# onehot_encode


values = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/-! '
char_to_int = dict((c, i) for i, c in enumerate(values))
int_to_char = dict((i, c) for i, c in enumerate(values))
data='ujfd'
int_encode = [char_to_int[char] for char in data]
num_string='0.'
for num in int_encode:
    num_string+=str(num)
deci=len(num_string)-2
#Comment

data_val="%."+str(deci)+"f" % float(num_string)

print (data_val)
