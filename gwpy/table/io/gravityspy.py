# -*- coding: utf-8 -*-
# Copyright (C) Scott Coughlin (2017)
#
# This file is part of GWpy.
#
# GWpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy.  If not, see <http://www.gnu.org/licenses/>.

"""Input/output methods for tabular data.

Access to GravitySpy and O1GlitchClassification triggers requires access
to a PostgresSQL database. Users can set the username and password for
connections in the following environment variables

- ``GRAVITYSPY_DATABASE_USER``
- ``GRAVITYSPY_DATABASE_PASSWORD``

These can be found https://secrets.ligo.org/secrets/144/. The description
is the username and thesecret is the password.
"""
import os

from astropy.table import Table

from .fetch import register_fetcher
from .. import GravitySpyTable
from .. import EventTable
from ..filter import (OPERATORS, parse_column_filters)

__author__ = 'Scott Coughlin <scott.coughlin@ligo.org>'


def get_gravityspy_triggers(tablename, engine=None, columns=None,
                            selection=None, **kwargs):
    """Fetch data into an `GravitySpyTable`

    Parameters
    ----------
    table : `str`,
        The name of table you are attempting to receive triggers
        from.

    selection
        other filters you would like to supply
        underlying reader method for the given format

    .. note::

       For now it will attempt to automatically connect you
       to a specific DB. In the future, this may be an input
       argument.

    Returns
    -------
    table : `GravitySpyTable`
    """
    import pandas as pd
    from sqlalchemy.engine import create_engine
    from sqlalchemy.exc import ProgrammingError

    # connect if needed
    if engine is None:
        conn_kw = {}
        for key in ('db', 'host', 'user', 'passwd'):
            try:
                conn_kw[key] = kwargs.pop(key)
            except KeyError:
                pass
        connectionStr = connectStr(**conn_kw)
        engine = create_engine(connectionStr)

    # parse columns for SQL query
    if columns is None:
        columnstr = '*'
    else:
        columnstr = ', '.join('"%s"' % c for c in columns)

    # parse selection for SQL query
    if selection is None:
        selectionstr = ''
    else:
        selections = []
        for col, def_ in parse_column_filters(selection):
            for thresh, op_ in def_:
                opstr = [key for key in OPERATORS if OPERATORS[key] is op_][0]
                selections.append('{0} {1} {2}'.format(col, opstr, thresh))
        if selections:
            selectionstr = 'where %s' % ' AND '.join(selections)

    # build SQL query
    qstr = 'SELECT %s FROM %s %s' % (columnstr, tablename, selectionstr)

    # perform query
    try:
        tab = pd.read_sql(qstr, engine, **kwargs)
    except ProgrammingError as e:
        if 'relation "%s" does not exist' % tablename in str(e):
            msg = e.args[0]
            msg = msg.replace(
                'does not exist',
                'does not exist, the following tablenames are '
                'acceptable:\n    %s\n' % '\n    '.join(engine.table_names()))
            e.args = (msg,)
        raise

    tab = Table.from_pandas(tab)

    # and return
    return GravitySpyTable(tab.filled())

# -- utilities ----------------------------------------------------------------


def connectStr(db='gravityspy', host='gravityspy.ciera.northwestern.edu',
               user=os.getenv('GRAVITYSPY_DATABASE_USER', None),
               passwd=os.getenv('GRAVITYSPY_DATABASE_PASSWD', None)):
    """Create string to pass to create_engine
    """

    if (not user) or (not passwd):
        raise ValueError('Remember to either pass '
                         'or export GRAVITYSPY_DATABASE_USER '
                         'and export GRAVITYSPY_DATABASE_PASSWD in order '
                         'to access the Gravity Spy Data: '
                         'https://secrets.ligo.org/secrets/144/'
                         ' description is username and secret is password.')

    connectionString = 'postgresql://{0}:{1}@{2}:5432/{3}'.format(
        user, passwd, host, db)

    return connectionString


register_fetcher('gravityspy', EventTable, get_gravityspy_triggers,
                 usage="tablename")
