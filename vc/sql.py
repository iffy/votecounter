from twisted.internet import defer
from twisted.python import log
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime
from sqlalchemy.sql import select

from collections import OrderedDict

from vc.error import NotAnOption

metadata = MetaData()

SchemaPatch = Table('_schema_patch', metadata,
    Column('name', String, primary_key=True),
    Column('created', DateTime),
)

Total = Table('total', metadata,
    Column('key', String, primary_key=True),
    Column('count', Integer),
    Column('updated', DateTime),
)
Vote = Table('vote', metadata,
    Column('id', Integer, primary_key=True),
    Column('created', DateTime),
    Column('key', String),
    Column('ip', String),
)


patches = OrderedDict()
patches['first'] = [
    '''CREATE TABLE _schema_patch (
        name text primary key,
        created timestamp default current_timestamp
    )''',
    '''CREATE TABLE total (
        key text primary key,
        count integer default 0,
        updated timestamp default current_timestamp
    )''',
    '''CREATE TABLE vote (
        id serial primary key,
        created timestamp default current_timestamp,
        key text,
        ip text
    )''',
    '''
    CREATE FUNCTION inc_vote_total() RETURNS trigger as $inc_vote_total$
    BEGIN
        -- Try update
        UPDATE total SET count = count + 1 WHERE key = NEW.key;
        IF found THEN
            RETURN NEW;
        END IF;

        -- Insert
        INSERT INTO total (key, count) VALUES (NEW.key, 1);
        RETURN NEW;
    END;
    $inc_vote_total$ LANGUAGE plpgsql;
    ''',
    '''
        CREATE TRIGGER inc_vote_total AFTER INSERT ON vote
        FOR EACH ROW EXECUTE PROCEDURE inc_vote_total();
    ''',
]




class SQLVoteStore(object):


    def __init__(self, engine, options):
        """
        @param options: List of allowed voting options.
        """
        self.engine = engine
        self.options = options


    @defer.inlineCallbacks
    def upgradeSchema(self):
        applied = []
        try:
            result = yield self.engine.execute(select([SchemaPatch.c.name]))
            rows = yield result.fetchall()
            applied = [x[0] for x in rows]
        except Exception as e:
            log.msg('Error fetching patches: %r' % (e,))
        for name, sqls in patches.items():
            if name in applied:
                continue
            conn = yield self.engine.connect()
            trans = yield conn.begin()
            try:
                log.msg('%r applying' % (name,), system='db')
                for sql in sqls:
                    yield conn.execute(sql)
                yield conn.execute(SchemaPatch.insert().values(name=name))
                yield trans.commit()
                log.msg('%r applied' % (name,), system='db')
            except Exception as e:
                yield trans.rollback()
                raise e


    def vote(self, option, ip):
        if option not in self.options:
            return defer.fail(NotAnOption('%r is not an option' % (option,)))
        return self.engine.execute(Vote.insert().values(key=option, ip=ip))


    @defer.inlineCallbacks
    def getResults(self):
        result = yield self.engine.execute(select([Total.c.key, Total.c.count]))
        rows = yield result.fetchall()
        ret = {}
        for option in self.options:
            ret[option] = 0
        for option, total in rows:
            ret[option] = total
        defer.returnValue(ret)


