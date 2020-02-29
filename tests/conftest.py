#!/usr/bin/env python

__author__ = "Patrick Godwin (patrick.godwin@psu.edu)"
__description__ = "global configuration for pytest suite"


import pytest


# example GCN circular from https://gcn.gsfc.nasa.gov/gcn3_circulars.html

GCN_TITLE = "GCN GRB OBSERVATION REPORT"
GCN_NUMBER = "40"
GCN_SUBJECT = "GRB980329 VLA observations"
GCN_DATE = "98/04/03 07:10:15 GMT"
GCN_FROM = "Greg Taylor at NRAO"
GCN_BODY = """
G.B. Taylor, D.A. Frail (NRAO), S.R. Kulkarni (Caltech), and
the BeppoSAX GRB team report:

We have observed the field containing the proposed x-ray counterpart
1SAX J0702.6+3850 of GRB 980329 (IAUC 6854) with the VLA at 8.4 GHz
on UT 1998 Mar 30.2, April 1.1, and April 2.1.  Observations on April
1.1 detected a radio source VLA J0702+3850 within the 1 arcminute
error circle of 1SAX J0702.6+3850.  The coordinates of
VLA J0702+3850 are: ra = 07h02m38.02170s dec = 38d50'44.0170" (equinox
J2000) with an uncertainty of 0.05 arcsec in each coordinate.  The
size of this radio source is less than 0.25 arcsec.  The density of
sources on the sky stronger than 250 microJy at this frequency is
0.0145 arcmin**-2.

The flux density measurements of VLA J0702+3850 are as follows:

Date(UT)   8.4 GHz Flux Density
--------   ----------------------
Mar 30.2   166 +/- 50 microJy
Apr  1.1   248 +/- 16    "
Apr  2.1    65 +/- 25    "

where the uncertainty in the measurement reflects the 1 sigma rms
noise in the image.  These measurements clearly demonstrate that
the radio source is variable on timescales of less than 1 day.
This rapid variability is similar to that observed in the
radio afterglow from GRB 970508.  We propose VLA J0702+3850
is the radio afterglow from GRB 980329.

Additional radio observations are in progress.
"""

GCN_CIRCULAR = f"""\
TITLE:   {GCN_TITLE}
NUMBER:  {GCN_NUMBER}
SUBJECT: {GCN_SUBJECT}
DATE:    {GCN_DATE}
FROM:    {GCN_FROM}

{GCN_BODY}\
"""


@pytest.fixture(scope="session")
def circular_text():
    return GCN_CIRCULAR


@pytest.fixture(scope="session")
def circular_msg():
    return {
        "header": {
            "title": GCN_TITLE,
            "number": GCN_NUMBER,
            "subject": GCN_SUBJECT,
            "date": GCN_DATE,
            "from": GCN_FROM,
        },
        "body": GCN_BODY,
    }
