from sqlalchemy import MetaData, Table, Column, Integer, String



class SQLVoteStore(object):


    def __init__(self, engine, options):
        """
        @param options: List of allowed voting options.
        """


    def upgradeSchema(self):
        pass


    def vote(self, option, ip):
        pass


    def getResults(self):
        pass


