import json
import basnet
import os,sys

# possible values
values = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/-! '
# dictionaries of char->int and int->char
char_to_int = dict((c, i) for i, c in enumerate(values))
int_to_char = dict((i, c) for i, c in enumerate(values))


def encode(data):
    # integer encoding (returns numerical representation of char)
    if type(data) is int or type(data) is NoneType:
        data = str(data)
    int_encode = [char_to_int[char] for char in data]
    # one hot encode
    onehot_encode = list()
    for value in int_encode:
        letter = [0 for _ in range(len(values))]
        letter[value] = 1
        onehot_encode.append(letter)
    return onehot_encode


# End encode


def decode(data):  # accepts a list
    index = 0;
    word = ''
    for row in data:
        index = 0;
        for element in row:
            if element != 0:
                word += (str(values[index]))
            index += 1

    return word


# End decode

def encode_all(training):
    if type(training) is dict:
        encode_data = {}
        for key, val in training.items():
            if type(val) is dict or type(val) is list:
                encode_data[key] = encode_all(val)  # recursion to find deepest level in dictionary
            else:
                encode_data[key] = encode(val)
        return encode_data
    elif type(training) is list:
        encode_data = []
        for val in training:
            if type(val) is dict or type(val) is list:
                encode_data.append(encode_all(val))  # recursion to find deepest level in dictionary
            else:
                encode_data.append(encode(val))
        return encode_data

    return 0

    # IN PROGRESS



def pull_data(data, desired):
    new_list = {}
    if type(data) is dict:
        for key, val in data.items():
            if type(val) is dict:
                to_add = pull_data(val,desired)  # Data type in value is another list or dict, so go another layer deeper
                for k, v in to_add.items():
                    new_list[k] = v
            else:
                if type(val) is list:  # Goes through lists to check for special cases wherein important dicts. lie within lists
                    for values in val:
                        if type(values) is dict:
                            to_add = pull_data(values, desired)
                            for k, v in to_add.items():
                                new_list[k] = v
                if key in desired:
                    new_list[key] = val

    return new_list
input_vals=['hostname','cluster','parentcluster','building','cloud','spec','manufacturer','dc','model','owners','tags']
def create_csv(input_data):
    try:
        with open('training_data.csv','x') as file:
            file.write('hostname,cluster,parentcluster,building,cloud,spec,manufacturer,dc,model,owners,tags,under_utilized')
            file.close()
    except:
        #File already exists

    for obj in input_data:
        csv_line=[]
        ind=0
        for key,val in obj:
            if key==input_vals[ind]:
                #Key is included, good to add
                csv_line.append(val)
            else:
                #Desired key missing: not found in manifest data. Add blank space
                csv_line.append("")
        csv_line=','.joing(csv_line)
        with open('training_data.csv','a') as file:
            file.write(csv_line)
            file.close()


directory='manifest_training'


client = basnet.BasClient("rhstsvc", 2, 9)
all_data=[]
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".manifest"):
        fileOpen=open(directory+'/'+filename).read()
        fulldata = json.loads(fileOpen)
        relevant = pull_data(fulldata, input_vals)
        #Write Request
        try:
            req = {"getMachine": relevant['hostname']
            #Send request & recieve data
            hosts = client.sendRequest(req)
            relevant['tags']=hosts['tags']
        except:
            #Machine is no longer in RHST-> Ignore tags
        #relevant = encode_all(relevant)
        #Adds each server object into the array containing all data
        all_data.append(relevant)
create_csv(all_data)
#Data is ready to go into .csv file

