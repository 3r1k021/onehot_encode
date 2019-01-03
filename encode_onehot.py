# input
data = '025/13'
#possible values
values = '0123456789abcdefghijklmnopqrstuvwxyz/- '
# dictionaries of char->int and int->char
char_to_int = dict((c, i) for i, c in enumerate(values))
int_to_char = dict((i, c) for i, c in enumerate(values))


def encode(data):
    # integer encoding (returns numerical representation of char)
    int_encode = [char_to_int[char] for char in data]
    # one hot encode ()
    onehot_encode = list()
    for value in int_encode:
    	letter = [0 for _ in range(len(values))]
        letter[value] = 1
        onehot_encode.append(letter)
    print(onehot_encode)
#End encode


def decode(data):
    # integer encoding (returns numerical representation of char)
    int_decode = [int_to_char[int] for int in data]
    # one hot encode ()
    onehot_decode = list()
    for value in int_decode:
    	letter = [0 for _ in range(len(values))]
        letter[value] = 1
        onehot_encode.append(letter)
    print(onehot_encode)
#End encode

encode('erik')