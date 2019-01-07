#possible values
values = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/-! '
# dictionaries of char->int and int->char
char_to_int = dict((c, i) for i, c in enumerate(values))
int_to_char = dict((i, c) for i, c in enumerate(values))


def encode(data):
    # integer encoding (returns numerical representation of char)
    if type(data) is int:
        data=str(data)
    int_encode = [char_to_int[char] for char in data]
    # one hot encode ()
    onehot_encode = list()
    for value in int_encode:
    	letter = [0 for _ in range(len(values))]
        letter[value] = 1
        onehot_encode.append(letter)
    return onehot_encode
#End encode


def decode(data):
    index=0;
    word=''
    for row in data:
        index=0;
        for element in row:
            if element!=0:
                word+=(str(values[index]))
            index+=1
            
    return word
#End encode

def encode_all(training):
    if type(training) is dict:
        encode_data={} 
        for key,val in training.items():
            if type(val) is dict or type(val) is list:
                encode_data[key]=encode_all(val)   #recursion to find deepest level in dictionary
            else:
                encode_data[key]=encode(val)
        return encode_data
    elif type(training) is list:
        encode_data=[]
        for val in training:
            if type(val) is dict or type(val) is list:
                encode_data.append(encode_all(val))   #recursion to find deepest level in dictionary
            else:
                encode_data.append(encode(val))
        return encode_data

    return 0
    
def decode_all(training):
    if type(training) is dict:
        decode_data={}
        for key,val in training.items():
            if type(val) is dict or type(val) is list:
                encode_all(val)  
                break
            else:
               return 0
        return encode_data
    elif type(training) is list:
        encode_data=[]
        for val in training:
            if type(val) is dict or type(val) is list:
                encode_data.append(encode_all(val))   #recursion to find deepest level in dictionary
            else:
                encode_data.append(encode(val))
        return encode_data

    return 0    
    
testerrr=encode_all({ "Qal": "Erik","nons": [3,4,5],"sal": [3,4,{"e": [3,4,5]}],"erikkk": 3})
for key,val in testerrr.items():
    print (key,val)