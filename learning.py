class Learn(object):

    def __init__(self):
        self.load()

    data = []

    # Determines similarity of strings: used for generalizing hostnames and other attributes during onehot encoding
    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    # Compares first letters of strings for special cases wherein same bases letters indicate similar attributes
    def first_letters(self, a, b):
        vals = [.5, .3, .25, -.1]
        for n in range(0, 4):
            c = 3 - n
            sub_a = a[:c]
            sub_b = b[:c]
            if SequenceMatcher(None, sub_a, sub_b).ratio() == 1.0:
                return vals[n]

    # Takes a list of words, then categorizes them into mini "similar" lists, based on the categorizing functions above
    def group_words(self, list_words):
        total = list_words
        similar_lists = []
        all_words = total
        while len(total) > 0:

            for word in all_words:
                if word in total:
                    sim = list()
                    sim.append(word)
                    total = np.delete(total, np.where(total == word))
                    for comp_word in total:
                        # Calculates ratio of similarity, threshold is currently set to .6 (can be adjusted accordingly)
                        if self.similar(word, comp_word) + self.first_letters(word, comp_word) > .6:
                            sim.append(comp_word)
                            # Adds word to "similar" list, then deletes it from the primary list
                            total = np.delete(total, np.where(total == comp_word))
                    similar_lists.append(sim)
                else:
                    continue
                    # Word is already in category

        # Returns one list, containing other smaller lists (of categorized words)
        return similar_lists

    # End String Sorting----------------------
    def prediction(self, single_line):
        # Single line will be used to predict at this point
        # Load model

        # Read input line into csv (concrete path, does not change)
        file_csv = '/bb/data/dcreaper/ml/training_data.csv'
        with open(file_csv, 'a') as file:
            file.write(('\n' + ','.join(single_line)) + ',0')
            file.close()

        full = load(file_csv, False)  # Do not train, only using for data conversion
        with open('/bb/data/dcreaper/ml/length.txt', 'r') as file:
            num_len = file.readline()
            file.close()
        model = None
        try:
            model = self.create_baseline(int(num_len))
            model.load_weights('/bb/data/dcreaper/reaper_model.h5')
        except Exception as e:
            print(e)
        # last line of new data from full data
        last_full = full[-1]
        # training_line=np.array([last_full[:-1]])

        with open(file_csv, "r") as f:
            lines = f.readlines()
            lines = lines[:-1]
            f.close()
        try:
            os.remove(file_csv)
        except Exception as e:
            print(e)
        with open(file_csv, "w", newline='') as f:
            for l in lines:
                if l is not '':
                    f.write(l)
            f.close()

        training_line = np.array([last_full])
        ones = False
        training_num = int(training_line.shape[1])
        while int(num_len) != training_num:

            if int(num_len) > training_num:
                training_line = np.array([np.append(training_line[0], 0)])
            else:
                if training_line[0][-1] == 1:
                    ones = True
                training_line = np.delete(training_line[0], -1)
                training_line = np.array([training_line])

            training_num = int(training_line.shape[1])
        if ones:
            training_line = np.delete(training_line[0], -1)
            training_line = np.array([training_line])
            training_line = np.array([np.append(training_line[0], 1)])

        pred = model.predict(training_line)
        try:
            return pred[0][0]
        except Exception as E:
            print(E)

        return -1

    # Creates the actual outline and framework for the model, does not train
    def create_baseline(self, current_size):
        # create model
        model = Sequential()
        model.add(Dense(15, input_dim=current_size, kernel_initializer='normal', activation='relu'))
        model.add(Dense(1, kernel_initializer='normal', activation='sigmoid'))
        # Compile model, using the the logarithmic loss function, and the Adam gradient optimizer
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        return model

    # Trains the model based on current data
    def train_model(self, x, y):
        model = self.create_baseline(len(x[0]))
        model.fit(x, y, epochs=100, batch_size=5, verbose=1)
        # Fits model according to x and y, training data passed in
        loss, acc_test = model.evaluate(x, y)
        print(acc_test)
        print(loss)
        model.save('/bb/data/dcreaper/reaper_model.h5')
        # Saves the model in memory
        with open('/bb/data/dcreaper/ml/length.txt', 'w') as file:
            # Records the current length of the training data in a text file
            file.write(str(len(x[0])))
            file.close()
        return model


    # Read data file


    def load(self, filen, train):
        self.data = pd.read_csv(filen, header=0)
        seed = 5
        np.random.seed(seed)

        # Select the columns to use for prediction in the neural network
        # prediction_var = ['hostname', 'cluster', 'parentcluster', 'cloud', 'spec', 'manu', 'model', 'building', 'owners',
        #                 'tags', 'purpose']
        # x = data[prediction_var].values
        y = self.data.under_utilized.values
        self.combine(self.one_hot_encoding(y), self.multi_label_binary_encoding(), self.string_encoding(y), y)




    def one_hot_encoding(self, y):
        # One-Hot Encoding------------------------------------------
        one_hot = [self.data.cloud.values, self.data.building.values, self.data.parentcluster.values,
                   self.data.spec.values,
                   self.data.manu.values,
                   self.data.purpose]
        n = 0
        onehot_narr = [[]]

        for big_col in one_hot:
            one_hot_data = []
            for col in big_col:
                one_hot_data.append([col])
            # End for loop

            onehotencoder = ce.OneHotEncoder(cols=[0])
            one_hot_encoded_data = onehotencoder.fit_transform(one_hot_data, y)
            if n != 0:
                onehot_narr = np.concatenate((onehot_narr, one_hot_encoded_data), axis=1)
            else:
                onehot_narr = one_hot_encoded_data
                # order+=one_hot_encoded_data.classes_
            n += 1
        return onehot_narr

        # End One-hot. Data stored in: onehot_nArr-------------------------------------

    def multi_label_binary_encoding(self):
        # MultiLabelBinary Encoding-------------------------------------------
        n = 0
        multilabel_arr = [[]]
        multi_data = [self.data.owners.values, self.data.tags.values]

        for col in multi_data:
            multi_fixed = []
            col_arr = []
            for strings in col:
                if strings is not 'null':
                    core = str(strings)[1:-1]  # Cuts off brackets
                    mini_row = core.split(' ')
                    mini_row = [c for c in mini_row if c is not '']
                    col_arr.append(mini_row)
                else:
                    col_arr.append(strings)
            multi_fixed.append(col_arr)

            for multi_col in multi_fixed:
                mlb = MultiLabelBinarizer()
                mlb_arr = mlb.fit_transform(multi_col)
                if n != 0:
                    multilabel_arr = np.concatenate((multilabel_arr, mlb_arr), axis=1)
                else:
                    multilabel_arr = mlb_arr
                n += 1
        return multilabel_arr
        # MultiLabelBinary Encoding end. Data stored in: multiLabel_arr-----------------


    def string_encoding(self, y):
        # String encoding-------------------------------------
        string_data = [self.data.hostname.values, self.data.cluster.values, self.data.model.values]
        full_str_enc = [[]]
        i = 0
        for col in string_data:
            orig_total = col
            grouped = self.group_words(col)
            for group in grouped:
                for word in group[1:]:
                    word += ''
                    orig_total = [group[0] if x in group else x for x in orig_total]
            onehotencoder = ce.OneHotEncoder(cols=[0])

            orig_total = onehotencoder.fit_transform(orig_total, y)
            if i != 0:
                full_str_enc = np.concatenate((full_str_enc, orig_total), axis=1)
            else:
                full_str_enc = orig_total
            i += 1
        return full_str_enc
        # End String encoding----------------------------------

    # Combine Data
    def combine(self, onehot_narr, multilabel_arr, full_str_enc, train, y):
        full_set = onehot_narr
        res_col = []
        for x in self.data.under_utilized.values:
            res_col.append([x])
        full_set = np.concatenate((full_set, multilabel_arr, full_str_enc), axis=1)
        full_set = np.concatenate((full_set, res_col), axis=1)  # Finally, adds in results
        x = full_set
        self.load.si = full_set.shape[1]
        if train is True:
            self.train_model(x, y)

        return full_set


