self.hostname = _hostname
        self.aliases = list()
        self.avg_underutil = None
        self.cpu_underutil = None
        self.mem_underutil = None
        self.netin_underutil = None
        self.netout_underutil = None
        self.dcid = None
        self.isvm = None
        self.manufacturer = None
        self.model = None
        self.sbb = None
        self.serial = None
        self.datacenter = None
        self.bdms_type = None
        self.uuids = list()
        self.datasources = list()
        self.oktodecom = False
        self.oktodecom_reason = None
        self.ignore = False
        self.powerdraw = 0
        self.updated = {"datasources": dict(), "fields": dict(), "object": None}
        self.cluster = None
        self.cluster_desc = None
        self.parentcluster = None
        self.parentcluster_desc = None
        self.inrhst = False
        self.bbenvup = False
        self.ips = list()
        self.cloud = None
        self.cloud_ip = None
        self.cloud_subnet = None
        self.networks = list()
        self.sec_group = None
        self.age = None
        self.san = None
        self.san_used = None
        self.ptp = None
        self.multicast = None
        self.multicast_type = None
        self.multicast_tags = list()
        self.os_type = None
        self.os_ver = None
        self.os_xos = None

class Gather(object):
    reaper_db = []

    def __init__(self, options, desired):
        reaper_db_conn = reaperdb.ReaperDB(options)
        global reaper_db
        reaper_db = reaper_db_conn.get_underutilized_hosts()

        # Successfully connected to DB
        self.pull_sqlite_data(options, desired)

    # End Init Method

    def match(self, desired, cols):
        numerical = []
        for name in cols:
            try:
                numerical.append(desired.index(name))
            except Exception as e:
                print(e)
        return numerical

    def gather_data(self, host, desired):
        try:
            sqr = "https://sor.bloomberg.com/sor/server/hostname/"
            request = sqr + host.hostname
            r = requests.get(request)
            req = r.json()['server']
            return pull_data(req, desired)
        except Exception as e:
            return e

    def create_csv(self, input_data):
        decom_count = 0
        nodecom_count = 0
        file_csv = '/bb/data/dcreaper/ml/training_data.csv'
        input_vals = ['hostname', 'cluster', 'parentcluster', 'cloud', 'spec', 'manu', 'model', 'building', 'owners',
                      'tags', 'purpose']
        try:
            os.remove(file_csv)
            # New CSV is rewritten every run
        except Exception as e:
            print(e)
            # Ignore, file is not created yet

        try:
            with open(file_csv, 'w') as file:
                file.write(','.join(input_vals) + ',under_utilized')
                file.close()
        except Exception as e:
            print(e)
        # File already exists

        nodecom_current = 0
        for line in input_data:
            for i, attr in enumerate(line):
                if i == len(line) - 1:
                    if attr == 0:
                        nodecom_count += 1
                    else:
                        decom_count += 1

        for line in input_data:

            str_line = ''
            for attr in line:
                str_line += str(attr) + ','
            # Line is ready
            str_line = str_line[0:-1]

            last_not_decom = False
            if int(str_line[-1]) == 0:
                last_not_decom = True

            if nodecom_current < int(decom_count + 5) or last_not_decom is False:
                if last_not_decom is True:
                    nodecom_current += 1
                with open(file_csv, 'a') as file:
                    file.write('\n' + str_line)
                    file.close()
        learn.load(file_csv, True)

        return 0

    # End Create CSV Method

    def predict(self, options, host_obj):
        print(host_obj)
        des = ['hostname', 'cluster', 'parent_cluster', 'cloud', 'spec',
               'manu', 'model', 'building', 'owners', 'tags', 'purpose']
        csv_line = list()
        csv_line.append(host_obj.hostname)
        csv_line.append(host_obj.cluster)
        csv_line.append(host_obj.parent_cluster)
        csv_line.append(host_obj.cloud)

        data = pull_data(host_obj, des)
        # Make into CSV-friendly format before passing to ML class
        return learn.prediction(data)

    def find_code(self):
        cur = self.get_column('drqs')
        for num in cur:
            try:
                code_is = int(num)
                return code_is
            except TypeError:
                continue

    def pull_sqlite_data(self, options, desired):
        rdb = reaper_db
        full_data = []
        good = 0
        client = basnet.BasClient("rhstsvc", 2, 9)
        full_selection = [line for line in rdb]  # All hostnames
        for current_host_index, host in enumerate(full_selection):
            sqlite_col = ['hostname', 'cluster', 'parent_cluster', '', 'sbb', 'manufacturer', 'model', 'datacenter',
                          'contacts']
            line = []
            host_attr = self.gather_data(host[0], desired)

            for ind, attr in enumerate(desired):
                if type(host_attr) is not dict:
                    # print ('not found in SOR')
                    nexta = 'null'
                else:
                    nexta = host_attr.get(attr, 'null')
                if nexta is 'null':
                    try:
                        full_attr_cols = self.get_column(sqlite_col[ind])

                        # full_attr_cols=
                        if sqlite_col[ind] is 'contacts':
                            con_arr = full_attr_cols[current_host_index].split(',')
                            nexta = '['
                            for wo in con_arr:
                                nexta += (wo + ' ')
                            nexta = nexta[0:-1] + ']'
                            # print (nextA)
                        else:
                            nexta = full_attr_cols[current_host_index]

                    except TypeError as e:
                        print(e)

                    #   print ('col not found')  #Still not found, remains null
                # Try to pull from DB now
                line.append(nexta)

            try:
                req = {"getMachine": host[0]}
                # Send request & recieve data
                hosts = client.sendRequest(req)
                line.append(hosts['machine']['tags'])
            except KeyError:
                line.append('null')

            full_data.append(line)

        # Now, gather the 'underutilized' determination from DRQS, using 'drqs' col values
        drqs_list = self.get_column('drqs')
        drqs_codes = []
        goods = []
        lost_rows = []
        for row, i in enumerate(drqs_list):
            try:
                index = int(i)
                goods.append(index)
                drqs_codes.append(index)
            except TypeError:
                lost_rows.append(row)
                try:
                    drqs_codes.append(goods[0])
                except TypeError:
                    drqs_codes.append(self.find_code())

        # num_chunks = (len(drqs_codes) + 19) / 30
        search_drqs = drqs.Drqs(options)
        ticket_cache = {}
        for iteration, chunk in enumerate(chunks(list(drqs_codes), 30)):
            # print('Querying DRQS chunk: %u / %u' % (iteration, num_chunks))
            ticket_cache.update(search_drqs.poll_drqssvc(options["drqs_creator_uuid"], chunk))
            # print('DRQS cache has %u items...' % len(ticket_cache))

        ticket_dict = {'wait': 0, 'vm': 1, 'igno': 0, 'deco': 1}

        index = 0

        tickets_all = list(ticket_cache.values())
        insert_count = 0
        while len(tickets_all) > 0:
            insert_count += 1
            if index in lost_rows:
                full_data[index].append('null')
            else:
                ticket = tickets_all[0]
                try:
                    full_data[index].append(ticket_dict[ticket['header']['function'].lower()])
                except Exception:
                    full_data[index].append('null')
                del (tickets_all[0])
            index += 1
        accom = insert_count

        if insert_count < len(drqs_codes):
            for l in range(insert_count, len(drqs_codes) - 1):
                accom += 1
                full_data[l].append('null')

        # Done getting indicators

        # Finally, check for manifest file needed to determine true underutilization

        # manifest_list=os.listdir('/lanserv/data/evictor/')
        # manifest_list = ['lanserv/data/evictor/' + item for item in manifest_list]

        manifest_list = os.listdir('evictor-new/')
        manifest_list = ['evictor-new/' + item for item in manifest_list]
        filelist = list(filter(lambda x: not os.path.isdir(x), manifest_list))
        serial_all = self.get_column('serial')
        all_list = self.get_column('aliases')
        for num, alias in enumerate(all_list):
            all_names = [full_data[num][0]]
            all_names.extend(list(alias[0].split(', ')))
            serial = serial_all[num]
            hostname_results = []
            serial_results = []
            for to_check in all_names:
                try:
                    if to_check is not '':
                        hostname_regex = re.compile(r"(" + to_check + r")\..*")
                        hostname_results = [m.group(0) for l in filelist for m in [hostname_regex.search(l)] if m]
                except TypeError as e:
                    print(e)
                if serial is not None:
                    try:
                        serial_regex = re.compile(r".*\.(" + serial + r")\..*")
                        serial_results = [m.group(0) for l in filelist for m in [serial_regex.search(l)] if m]
                    except TypeError as e:
                        print(e)

                if len(hostname_results) > 0 or len(serial_results) > 0:
                    break

            if len(hostname_results) > 0 or len(serial_results) > 0:
                good += 1
                full_data[num].append(1)
            else:
                full_data[num].append(0)
        # print ('decom: '+str(good)+'   no decom: '+str(bad))

        # Put everything together
        full = full_data
        for row_ind, row_vals in enumerate(full):
            for item_ind, item in enumerate(row_vals):
                if type(item) is list:
                    full_data[row_ind][item_ind] = to_string(item)
        # Converts all to strings for CSV
        self.create_csv(full_data)
        return full_data

    def get_column(self, title):
        global reaper_db
        db_cols = ['hostname', 'entry_date', 'aliases', 'contacts', 'age', 'datacenter', 'cluster', 'parent_cluster',
                   'manufacturer', 'model', 'serial', 'sbb', '', '', '', '', '', '', '', '', '', 'drqs']
        ind = db_cols.index(title)
        line = []
        for machine in reaper_db:
            line.append(machine[ind])
        return line

    # print (full_data)


#            if more==1#More info is needed to fill all columns--Check database
#    full_data.append(line)

def to_string(arr):
    string = '['
    for a in arr:
        string += a + ' '
    string = string[0:-1] + ']'
    return string


# End function: array to string

def chunks(l, n):
    """
    Yield n-sized chunks from the list l
    :param l:
    :param n:
    :return:
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]


# End chunks

def pull_data(data, desired):
    try:
        new_list = {}
        if type(data) is dict:
            for key, val in data.items():
                if type(val) is dict:
                    to_add = pull_data(val,
                                       desired)
                    for k, v in to_add.items():
                        if k not in new_list:
                            new_list[k] = v
                else:
                    if type(
                            val) is list:
                        for values in val:
                            if type(values) is dict:
                                to_add = pull_data(values, desired)
                                for k, v in to_add.items():
                                    if k not in new_list:
                                        new_list[k] = v
                    if key in desired:
                        if key not in new_list:
                            new_list[key] = val
        return new_list
    except Exception as e:
        print(e)
        return e


"""
options = dict()
options['sqlite_dbfile'] = '/bb/data/dcreaper/db/dc-reaper-dev.sqlite'
options['use_basnet_proxy'] = False
options['db_use_sqlite'] = False
options['db_use_comdb2'] = True
options['comdb2_name'] = 'reaperdb'
options['comdb2_tier'] = 'dev'
options['db_ignore_expiration'] = 3
options['drqs_app'] = 'dcreaper:09936FE9191C96E4224D9CC51FBDEFCF'
options['drqs_service_uuid'] = 93318970
options['drqs_creator_uuid'] = 23191190
# Use this later in "classifier" file to call this script
test_obj = Gather(options,
                  ['hostname', 'cluster', 'parent_cluster', 'cloud', 'system_spec', 'manufacturer', 'model', 'building',
                   'owners'])
"""
