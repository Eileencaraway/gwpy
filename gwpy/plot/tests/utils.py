# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2018)
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

"""Utilities for testing `gwpy.plot`
"""

from six.moves import StringIO

import pytest

from matplotlib import (pyplot, rc_context)

from ..tex import HAS_TEX
from .. import Plot


@pytest.fixture(scope='function', autouse=True, params=[
    pytest.param(False, id='no-tex'),
    pytest.param(True, id='usetex', marks=pytest.mark.skipif(
        not HAS_TEX, reason='no latex')),
])
def usetex(request):
    """Fixture to test plotting function with and without `usetex`

    Returns
    -------
    usetex : `bool`
        the value of the `text.usetex` rcParams settings
    """
    use_ = request.param
    with rc_context(rc={'text.usetex': use_}):
        yield use_


class _Base(object):
    @staticmethod
    def save(fig, format='png'):
        out = StringIO()
        fig.savefig(out, format=format)
        return fig

    @classmethod
    def save_and_close(cls, fig, format='png'):
        cls.save(fig, format=format)
        try:
            fig.close()
        except AttributeError:
            pyplot.close(fig)
        return fig


class FigureTestBase(_Base):
    FIGURE_CLASS = Plot

    @classmethod
    @pytest.fixture(scope='function')
    def fig(cls):
        """Yield a new figure of type ``FIGURE_CLASS`` and check that
        it saves as png after the test function finishes
        """
        fig = pyplot.figure(FigureClass=cls.FIGURE_CLASS)
        yield fig
        cls.save_and_close(fig)


class AxesTestBase(_Base):
    AXES_CLASS = Plot

    @classmethod
    @pytest.fixture(scope='function')
    def ax(cls):
        fig = pyplot.figure(FigureClass=getattr(cls, 'FIGURE_CLASS', Plot))
        yield fig.gca(projection=cls.AXES_CLASS.name)
        cls.save_and_close(fig)
