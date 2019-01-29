
import numpy
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
#from IPython import get_ipython
#get_ipython().run_line_magic('matplotlib','inline')
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from keras.models import Sequential
from keras.layers import Dense
from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score

# Read data file
data = pd.read_csv("training.csv", header=0)
seed = 5
numpy.random.seed(seed)

# Select the columns to use for prediction in the neural network
prediction_var = ['hostname', 'cluster', 'parentcluster','building','cloud','spec','manufacturer','dc','model','owners','tags']
X = data[prediction_var].values
Y = data.under_utilized.values

# Diagnosis values are strings. Changing them into numerical values using LabelEncoder.
encoder = LabelEncoder()
encoder.fit(Y)
encoded_Y = encoder.transform(Y)

order=[]

#One-Hot Encoding------------------------------------------
one_hot=[data.building.values,   data.cloud.values,   data.dc.values]

n=0
onehot_nArr=numpy.array([])
for big_col in one_hot:
    one_hot_data=[]
    for col in one_hot[n]:
        one_hot_data.append([col])
        if n!=0:
            onehot_nArr=np.hstack(onehot_nArr,numpy.array(one_hot_data))
    onehot_nArr=numpy.array(one_hot_data)
    n+=1
    
#Initial condition
onehotencoder = OneHotEncoder(categorical_features = [0])
x = onehotencoder.fit_transform(one_hot_data).toarray() 

#Iterates rest of data from here
count=len(a)-1
while count>0:
    onehotencoder = OneHotEncoder(categorical_features = [-count])
    x = onehotencoder.fit_transform(one_hot_data).toarray()
    count-=1
order+=x.classes_
#End One-Hot Encoding-----------------------------------------




#MultiLabelBinarizer Encoding-----------------------------------

multi_data=[data.owners.values, data.tags.values]
for multi_cols in multi_data:
    mlb = MultiLabelBinarizer()
    mlb.fit_transform([x for x in multi_cols])
    #mlb is now expanded with multilabelbinarizer encoding
    order+=mlb.classes_

#End MultiLabelBinarizer Encoding--------------------------------


# Baseline model for the neural network. We choose a hidden layer of 10 neurons. The lesser number of neurons helps to eliminate the redundancies in the data and select the more important features.
def create_baseline():
    # create model
    model = Sequential()
    model.add(Dense(15, input_dim=11, kernel_initializer='normal', activation='relu'))
    model.add(Dense(1, kernel_initializer='normal', activation='sigmoid'))
    # Compile model. We use the the logarithmic loss function, and the Adam gradient optimizer.
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model


# Evaluate model using standardized dataset.
estimators = []
estimators.append(('standardize', StandardScaler()))
estimators.append(('mlp', KerasClassifier(build_fn=create_baseline, epochs=100, batch_size=5, verbose=0)))
pipeline = Pipeline(estimators)
kfold = StratifiedKFold(n_splits=5, shuffle=True)
results = cross_val_score(pipeline, X, encoded_Y, cv=kfold)
print("Results: %.2f%% (%.2f%%)" % (results.mean()*100, results.std()*100))

