import pytest
from bloomberg.dcsi.dcreaper.collector import bdmshosts

OPTIONS = dict()
OPTIONS['collector_log_level'] = "DEBUG"

bdms = bdmshosts.BDMSHosts(OPTIONS)
assert bdms.datasource is 'bdms'

def test_get_bdms_obj_good():

def test_get_bdms_obj_bad():

    assert True

def test_create_host_search():
    assert True


def test_create_hardware_search():
    assert True


def test_run_host_search():
    assert True


def test_run_hardware_search():
    assert True


def test_populate_data():
    assert True
























"""
bdmshosts.py
BDMS Dictionary class
Gathers hostnames and associated host metadata from BDMS
"""

import logging
import time
from ..hostdict import HostDict
from bloomberg.blimp import bdms
from bloomberg.dcsi import bpv

LOG = logging.getLogger(__name__)


class BDMSHosts(HostDict):
    """
    Defines a HostDict object which is a dictionary of Host objects,
    keyed by each Host object's hostname
    """

    def __init__(self, _options):
        """
        class constructor
        """
        HostDict.__init__(self, _options)

        # read options from config
        self.options = _options

        # set the logging level
        loglevel = logging.INFO

        if "collector_log_level" in self.options:
            collector_loglevel = eval("logging." + self.options['collector_log_level'])

            if collector_loglevel is not None:
                loglevel = collector_loglevel

        else:
            LOG.info("Collector logging level not defined in config - setting to INFO")

        logging.getLogger(__name__).setLevel(loglevel)

        self.datasource = "bdms"
        LOG.debug("Creating %s datasource", self.datasource)

        self.bdms_obj = None

    def __repr__(self):
        """
        Overload built-in method
        :return: datasource type
        """
        return "BDMSDict"

    def get_bdms_obj(self, _env):
        """
        Returns a BDMS object
        :param _env: environment (qa or prod)
        :return: bdms object
        """
        if _env == "prod":
            bdms_env = "prod"
        else:
            bdms_env = "qa"

        bdms_obj = bdms.Bdms(bpv.get_by_id(self.options["bdms_rw_client_id"],
                                           self.options["bpv_cert"],
                                           self.options["bpv_key"])[0],
                             bpv.get_by_id(self.options["bdms_rw_client_secret"],
                                           self.options["bpv_cert"],
                                           self.options["bpv_key"])[0],
                             bdms_env,
                             proxies={"https": "http://bproxy.tdmz1.bloomberg.com:80"})
        return bdms_obj

    def _create_host_search(self):
        """
        Returns a host search query structure
        :return: bdms search specification
        """
        criteria = self.bdms_obj.items.get_dynamic_search_criteria()["BDMSResponseData"]
        criteria["DatasetID"] = "Items"
        criteria["DataLoadLevel"] = bdms.ItemLoadLevel.DerivedHardware.value
        criteria["ResultsFormat"] = "ItemDetails"
        criteria["ItemSearchGlobalCriteria"] = {
            "ExcludeTrash": "True",
            "ExcludeTemplates": "True",
            "LimitToTemplates": "False",
            "ExcludePlannedItems": "True",
            "LimitToPlannedItems": "False"
        }
        criteria["PaginationDetails"]["PageSize"] = 1000
        criteria["groups"] = [
            {
                "op": "and",
                "rules": [
                    {
                        "op": "",
                        "condition": "Equal To",
                        "field": "Item.ItemType.Id",
                        "data": 122,  # host or logical host
                    }
                ]
            }
        ]
        return criteria

    def _create_hardware_search(self, hardwares):
        """
        Helper fuction for bulk_location_search that creates a BDMS custom search
        specifically aimed to get derived hardware information of host records
        Receives:
            hosts (lst): list of host names
        Returns:
            search_obj (dct): the custom search object for the BDMS custom search
            module that gets back the derived hardware information for each record
        """
        # initialize the search object
        criteria = self.bdms_obj.items.get_dynamic_search_criteria()["BDMSResponseData"]
        criteria["DatasetID"] = "Items"
        criteria["DataLoadLevel"] = 1024 + 128 + 64 + 32 + 16
        criteria["ResultsFormat"] = "ItemDetails"
        criteria["ItemSearchGlobalCriteria"] = {
            "ExcludeTrash": "True",
            "ExcludeTemplates": "True",
            "LimitToTemplates": "False",
            "ExcludePlannedItems": "True",
            "LimitToPlannedItems": "False",
            "AttributeNames": ["received.date", "system.spec"]
        }
        criteria["PaginationDetails"]["PageSize"] = 1000
        criteria["groups"] = [
                {
                    "op": "",
                    "rules": [
                        {
                            "op": "",
                            "condition": "In List",
                            "field": "Item.Id",
                            "data": hardwares,
                            "groups": []
                        }
                    ]
                }
            ]
        return criteria

    def run_host_search(self):
        """
        Runs a host search query against BDMS
        :return: query results
        """

        query_results = None

        try:
            # create the BDMS search object
            self.bdms_obj = self.get_bdms_obj(self.options["stage"])

            # run the query against BDMS
            hostsearch = self._create_host_search()

            query_results = self.bdms_obj.items.search(hostsearch, autopage=True)

        except Exception as e:
            LOG.critical("BDMS host search exception: %s", e)

        results = list()

        for result in query_results["BDMSResponseData"]["Results"]:
            results.append(result)

        LOG.debug("BDMS results received: %d", len(results))
        return results

    def run_hardware_search(self, items):
        """
        :param items:
        :return:
        """
        self.bdms_obj = self.get_bdms_obj(self.options["stage"])

        try:
            hardwaresearch = self._create_hardware_search(items)
            hardware_results = self.bdms_obj.items.search(hardwaresearch, autopage=True)
        except Exception as e:
            LOG.error("Hardware search exception: %s", str(e))
            return 1

        results = list()
        for result in hardware_results["BDMSResponseData"]["Results"]:
            results.append(result)

        return results

    def populate_data(self):
        """
        Populates hostnames in the hosts dictionary with results from BDMS
        :return: boolean pass/fail
        """
        start_time = time.time()

        # run the query against BDMS
        query_results = self.run_host_search()

        hardware_to_search = []

        if query_results is None:
            LOG.critical("BDMS host query failed")
            return 1

        # loop through the query results
        for item in query_results:

            # if DerivedHardware is empty, it's not a "host"
            if len(item['DerivedHardware']) == 0:
                LOG.debug("DerivedHardware empty for %s", item['DisplayName'])

            else:
                if item['DCID'] is not None:
                    # add the host to the host dictionary keyed by DCID
                    hostname_to_add = item['DCID'].lower()
                    LOG.debug("Adding host from BDMS: %s",  hostname_to_add)
                    self.add_host(hostname_to_add)

                    # add DCID is an alias
                    if item['DCID'] is not None and len(item['DCID']) > 0:
                        self.hosts[hostname_to_add].aliases.append(hostname_to_add)

                    # add Name as an alias
                    if item['Name'] is not None and len(item['Name']) > 0:
                        LOG.debug("Adding BDMS Name %s as an alias for %s", item['Name'].lower(), hostname_to_add)
                        self.hosts[hostname_to_add].aliases.append(item['Name'].lower())

                    # add DisplayName as an alias
                    if item['DisplayName'] is not None and len(item['DisplayName']) > 0:
                        LOG.debug("Adding BDMS DisplayName %s as an alias for %s",
                                  item['DisplayName'].lower(), hostname_to_add)
                        self.hosts[hostname_to_add].aliases.append(item['DisplayName'].lower())

                    # add aliases from BDMS
                    if item['HostAliases'] is not None:
                        LOG.debug("Adding BDMS HostAliases %s as aliases for %s",
                                  map(lambda x: x.lower(), item['HostAliases']), hostname_to_add)
                        self.hosts[hostname_to_add].aliases.extend(map(lambda x: x.lower(), item['HostAliases']))

                    # remove duplicates from aliases
                    self.hosts[hostname_to_add].aliases = list(set(self.hosts[hostname_to_add].aliases))

                    # keep list of hosts on which to perform a BDMS "hardware" search
                    hardware_to_search.extend([hw["ItemId"] for hw in item["DerivedHardware"]])

        hardware_results = self.run_hardware_search(hardware_to_search)
        for hardware_entry in hardware_results:

            if len(hardware_entry["DerivedHosts"]) == 1:
                hostname_to_add = hardware_entry["DerivedHosts"][0]["DCID"].lower()

                if "ItemManufacturer" in hardware_entry:

                    if "Name" in hardware_entry["ItemManufacturer"]:
                        LOG.debug("Adding BMDS Manufacturer %s for %s",
                                  hardware_entry['ItemManufacturer']['Name'], hostname_to_add)
                        self.hosts[hostname_to_add].manufacturer = hardware_entry['ItemManufacturer']['Name']

                    if "Name" in hardware_entry["Model"]:
                        LOG.debug("Adding BMDS Model %s for %s", hardware_entry['Model']['Name'], hostname_to_add)
                        self.hosts[hostname_to_add].model = hardware_entry['Model']['Name']

                    for attribute in hardware_entry["ItemAttributes"]:
                        if attribute['Name'] == "system.spec":
                            LOG.debug("Adding BMDS SBB %s for %s", attribute['Value'], hostname_to_add)
                            self.hosts[hostname_to_add].sbb = attribute['Value']

        LOG.info("BDMS hosts datasource populate_data execution time: %s seconds",
                 str(round(time.time() - start_time, 2)))




































      from bloomberg.dcsi.dcreaper.collector import hostdict

NUM_OF_HOSTS = 10

OPTIONS = dict()
OPTIONS['collector_log_level'] = "DEBUG"


def test_add_host():
    hdict = hostdict.HostDict(OPTIONS)

    # test adding 5 host entries
    for i in range(0, NUM_OF_HOSTS):
        hdict.add_host("testhost" + str(i))
    assert hdict.len() == NUM_OF_HOSTS
    for i in range(0, NUM_OF_HOSTS):
        assert hdict.hosts["testhost" + str(i)].hostname == "testhost" + str(i)

    # test adding a duplicate entry - there should be no changes
    hdict.add_host("testhost3", aliases=False)
    assert hdict.len() == NUM_OF_HOSTS
    assert hdict.hosts['testhost4'].hostname == "testhost4"

    # add host with alias
    hdict.add_host("n200", aliases=False)
    hdict.hosts["n200"].aliases = ['n200fddi', 'dcid1000126']
    assert hdict.len() == NUM_OF_HOSTS + 1
    assert hdict.hosts['n200'].hostname == "n200"
    assert hdict.hosts['n200'].aliases == ['n200fddi', 'dcid1000126']


def test_add_host_data():
    hdict = hostdict.HostDict(OPTIONS)

    # add 5 host entries, and add dcid for testhost4
    for i in range(0, NUM_OF_HOSTS):
        hdict.add_host("testhost" + str(i))
    assert hdict.len() == NUM_OF_HOSTS
    assert hdict.hosts['testhost4'].hostname == "testhost4"
    hdict.add_host_data("testhost4", "dcid", "dcid0004")
    assert hdict.hosts['testhost4'].dcid == "dcid0004"


"""
def test_add_aliases():
    with LogCapture() as logs:
        hdict = hostdict.HostDict(OPTIONS)
        hdict.datasource = "test"
        hdict.add_host("n200", aliases=False)
        hdict.add_host("devxnj501", aliases=False)
        hdict.add_host("devxob507", aliases=False)
        hdict.add_host("notahost", aliases=False)
        hdict.add_aliases()
        assert hdict.hosts['n200'].aliases == ['dcid1000126', 'n200fddi']
        assert hdict.hosts['devxnj501'].aliases == ['dcid0007608']
        assert hdict.hosts['devxob507'].aliases == ['dcid2000016']
        logs.check(('collector.hostdict', 'DEBUG', 'Adding n200 to the host dictionary test'),
                   ('collector.hostdict', 'DEBUG', 'Adding devxnj501 to the host dictionary test'),
                   ('collector.hostdict', 'DEBUG', 'Adding devxob507 to the host dictionary test'),
                   ('collector.hostdict', 'DEBUG', 'Adding notahost to the host dictionary test'),
                   ('collector.hostdict', 'DEBUG', "Adding aliases ['dcid0007608'] for devxnj501"),
                   ('collector.hostdict', 'DEBUG', "Adding aliases ['n200fddi', 'dcid1000126'] for n200"),
                   ('collector.hostdict', 'DEBUG', 'notahost: [Errno -2] Name or service not known'),
                   ('collector.hostdict', 'DEBUG', "Adding aliases ['dcid2000016'] for devxob507"))
"""


def test_merge():
    hdict1 = hostdict.HostDict(OPTIONS)
    hdict2 = hostdict.HostDict(OPTIONS)

    for i in range(0, int(NUM_OF_HOSTS / 2)):
        hdict1.add_host("testhost" + str(i))
    for i in range(int(NUM_OF_HOSTS / 2), NUM_OF_HOSTS):
        hdict2.add_host("testhost" + str(i))

    assert hdict1.len() == NUM_OF_HOSTS / 2
    assert hdict2.len() == NUM_OF_HOSTS / 2
    hdict1.merge(hdict2)
    assert hdict1.len() == NUM_OF_HOSTS
    for i in range(0, NUM_OF_HOSTS):
        assert hdict1.hosts['testhost' + str(i)].hostname == "testhost" + str(i)


def test_deduplicate():
    # create hosts with the same aliases - deduplicated should only be 1 host
    # with 10 aliases
    hdict = hostdict.HostDict(OPTIONS)
    for i in range(0, NUM_OF_HOSTS):
        hdict.add_host("testhost" + str(i))
        hdict.hosts['testhost' + str(i)].aliases.append("alias1")
    hdict.deduplicate()
    assert hdict.len() == 1
    assert len(hdict.hosts["testhost0"].aliases) == 10

    # create hosts with aliases that match other hostnames
    hdict2 = hostdict.HostDict(OPTIONS)
    for i in range(0, NUM_OF_HOSTS):
        hdict2.add_host("testhost" + str(i))
        hdict2.hosts['testhost' + str(i)].aliases.append("testhost" + str(NUM_OF_HOSTS - i - 1))
    assert hdict2.len() == NUM_OF_HOSTS
    hdict2.deduplicate()
    assert hdict2.len() == NUM_OF_HOSTS / 2


def test_merge_hosts():
    hdict = hostdict.HostDict(OPTIONS)
    hdict.add_host("source")
    hdict.add_host("dest")
    assert hdict.len() == 2

    hdict.hosts["source"].aliases = ["source_alias1", "source_alias2"]
    hdict.hosts["source"].serial = "12345"
    hdict.hosts["source"].datasources = ['sor']
    hdict.hosts["source"].manufacturer = "hp"

    hdict.hosts["dest"].aliases = ["dest_alias1", "dest_alias2"]
    hdict.hosts["dest"].serial = "12345"
    hdict.hosts["dest"].datasources = ['rhst']
    hdict.hosts["dest"].isvm = False
    hdict.hosts["dest"].inrhst = True

    hdict.merge_hosts("source", "dest")
    assert hdict.len() == 1
    assert set(hdict.hosts["dest"].aliases).difference({'dest_alias1', 'dest_alias2',
                                                        'source', 'source_alias1', 'source_alias2'}) == set()


def test_sanitize_hostnames():
    hdict = hostdict.HostDict(OPTIONS)
    hdict.add_host("dcid12345")
    hdict.hosts["dcid12345"].aliases.append("dcid12345")
    assert hdict.hosts["dcid12345"].aliases == ["dcid12345"]
    hdict.sanitize_hostnames()
    # confirm that aliases which are the same as the hostname are removed
    assert hdict.hosts["dcid12345"].aliases == []
    hdict.hosts["dcid12345"].aliases.append("testalias")
    assert hdict.hosts["dcid12345"].aliases == ["testalias"]
    hdict.sanitize_hostnames()
    assert hdict.hosts["dcid12345"].hostname == "testalias"
    assert hdict.hosts["dcid12345"].aliases == ["dcid12345"]
