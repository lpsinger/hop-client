from collections import defaultdict
from contextlib import contextmanager
import io
import os
import stat
from unittest.mock import MagicMock

import pytest

from hop import models
from hop.io import StartPosition


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

VOEVENT_XML = """\
<?xml version='1.0' encoding='UTF-8'?>
<voe:VOEvent xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:voe="http://www.ivoa.net/xml/VOEvent/v2.0" xsi:schemaLocation="http://www.ivoa.net/xml/VOEvent/v2.0 http://www.ivoa.net/xml/VOEvent/VOEvent-v2.0.xsd" version="2.0" role="observation" ivorn="ivo://gwnet/LVC#S200302c-1-Preliminary">
  <Who>
    <Date>2020-03-02T02:00:09</Date>
    <Author>
      <contactName>LIGO Scientific Collaboration and Virgo Collaboration</contactName>
    </Author>
  </Who>
  <What>
    <Param dataType="int" name="Packet_Type" value="150">
      <Description>The Notice Type number is assigned/used within GCN, eg type=150 is an LVC_PRELIMINARY notice</Description>
    </Param>
    <Param dataType="int" name="internal" value="0">
      <Description>Indicates whether this event should be distributed to LSC/Virgo members only</Description>
    </Param>
    <Param dataType="int" name="Pkt_Ser_Num" value="1">
      <Description>A number that increments by 1 each time a new revision is issued for this event</Description>
    </Param>
    <Param dataType="string" name="GraceID" ucd="meta.id" value="S200302c">
      <Description>Identifier in GraceDB</Description>
    </Param>
    <Param dataType="string" name="AlertType" ucd="meta.version" value="Preliminary">
      <Description>VOEvent alert type</Description>
    </Param>
    <Param dataType="int" name="HardwareInj" ucd="meta.number" value="0">
      <Description>Indicates that this event is a hardware injection if 1, no if 0</Description>
    </Param>
    <Param dataType="int" name="OpenAlert" ucd="meta.number" value="1">
      <Description>Indicates that this event is an open alert if 1, no if 0</Description>
    </Param>
    <Param dataType="string" name="EventPage" ucd="meta.ref.url" value="https://gracedb.ligo.org/superevents/S200302c/view/">
      <Description>Web page for evolving status of this GW candidate</Description>
    </Param>
    <Param dataType="string" name="Instruments" ucd="meta.code" value="H1,V1">
      <Description>List of instruments used in analysis to identify this event</Description>
    </Param>
    <Param dataType="float" name="FAR" ucd="arith.rate;stat.falsealarm" unit="Hz" value="9.349090689402942e-09">
      <Description>False alarm rate for GW candidates with this strength or greater</Description>
    </Param>
    <Param dataType="string" name="Group" ucd="meta.code" value="CBC">
      <Description>Data analysis working group</Description>
    </Param>
    <Param dataType="string" name="Pipeline" ucd="meta.code" value="gstlal">
      <Description>Low-latency data analysis pipeline</Description>
    </Param>
    <Param dataType="string" name="Search" ucd="meta.code" value="AllSky">
      <Description>Specific low-latency search</Description>
    </Param>
    <Group name="GW_SKYMAP" type="GW_SKYMAP">
      <Param dataType="string" name="skymap_fits" ucd="meta.ref.url" value="https://gracedb.ligo.org/api/superevents/S200302c/files/bayestar.fits.gz,0">
        <Description>Sky Map FITS</Description>
      </Param>
    </Group>
    <Group name="Classification" type="Classification">
      <Param dataType="float" name="BNS" ucd="stat.probability" value="0.0">
        <Description>Probability that the source is a binary neutron star merger (both objects lighter than 3 solar masses)</Description>
      </Param>
      <Param dataType="float" name="NSBH" ucd="stat.probability" value="0.0">
        <Description>Probability that the source is a neutron star-black hole merger (primary heavier than 5 solar masses, secondary lighter than 3 solar masses)</Description>
      </Param>
      <Param dataType="float" name="BBH" ucd="stat.probability" value="0.8895532192171397">
        <Description>Probability that the source is a binary black hole merger (both objects heavier than 5 solar masses)</Description>
      </Param>
      <Param dataType="float" name="MassGap" ucd="stat.probability" value="0.0">
        <Description>Probability that the source has at least one object between 3 and 5 solar masses</Description>
      </Param>
      <Param dataType="float" name="Terrestrial" ucd="stat.probability" value="0.11044678078286028">
        <Description>Probability that the source is terrestrial (i.e., a background noise fluctuation or a glitch)</Description>
      </Param>
      <Description>Source classification: binary neutron star (BNS), neutron star-black hole (NSBH), binary black hole (BBH), MassGap, or terrestrial (noise)</Description>
    </Group>
    <Group name="Properties" type="Properties">
      <Param dataType="float" name="HasNS" ucd="stat.probability" value="0.0">
        <Description>Probability that at least one object in the binary has a mass that is less than 3 solar masses</Description>
      </Param>
      <Param dataType="float" name="HasRemnant" ucd="stat.probability" value="0.0">
        <Description>Probability that a nonzero mass was ejected outside the central remnant object</Description>
      </Param>
      <Description>Qualitative properties of the source, conditioned on the assumption that the signal is an astrophysical compact binary merger</Description>
    </Group>
  </What>
  <WhereWhen>
    <ObsDataLocation>
      <ObservatoryLocation id="LIGO Virgo"/>
      <ObservationLocation>
        <AstroCoordSystem id="UTC-FK5-GEO"/>
        <AstroCoords coord_system_id="UTC-FK5-GEO">
          <Time unit="s">
            <TimeInstant>
              <ISOTime>2020-03-02T01:58:11.519119</ISOTime>
            </TimeInstant>
          </Time>
        </AstroCoords>
      </ObservationLocation>
    </ObsDataLocation>
  </WhereWhen>
  <Description>Report of a candidate gravitational wave event</Description>
  <How>
    <Description>Candidate gravitational wave event identified by low-latency analysis</Description>
    <Description>V1: Virgo 3 km gravitational wave detector</Description>
    <Description>H1: LIGO Hanford 4 km gravitational wave detector</Description>
  </How>
</voe:VOEvent>\
"""

MESSAGE_BLOB = "This is a sample blob message. It is unstructured and does not require special parsing."

# This was the original configuration structure, which permitted only a single credential
AUTH_CONFIG_LEGACY = """\
[auth]
username = "username"
password = "password"
"""

# This is the new configuration structure, which contains a list of credentials
AUTH_CONFIG = """
auth = [{
         username="username",
         password="password"
         }]
"""


class MockBroker:
    """Mock a Kafka broker.

    This stores internally messages and tracks offsets
    for different consumer groups.

    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._messages = defaultdict(list)
        self._offsets = defaultdict(dict)

    def write(self, topic, msg, headers=[]):
        self._messages[topic].append((msg, headers))

    def has_message(self, topic, message, headers=[]):
        return (message, headers) in self._messages[topic]

    def read(self, topics, groupid, start_at=StartPosition.EARLIEST, **kwargs):
        if isinstance(topics, str):
            topics = [topics]

        for topic in topics:
            if topic not in self._offsets or groupid not in self._offsets[topic]:
                if start_at == StartPosition.EARLIEST:
                    self._offsets[topic][groupid] = 0
                else:
                    self._offsets[topic][groupid] = len(self._messages[topic]) - 1

            try:
                offset = self._offsets[topic][groupid]
                self._offsets[topic][groupid] += 1
                yield from self._messages[topic][offset:]
            except IndexError:
                pass


@pytest.fixture(scope="session")
def mock_broker():
    return MockBroker()


@pytest.fixture(scope="session")
def mock_producer():
    def _mock_producer(mock_broker, topic):
        class ProducerBrokerWrapper:
            def __init__(self, broker, topic):
                self.broker = broker
                self.topic = topic

            def write(self, msg, headers=[], delivery_callback=None):
                self.broker.write(self.topic, msg, headers)

            def close(self):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                pass

        producer = ProducerBrokerWrapper(mock_broker, topic)
        return producer

    return _mock_producer


@pytest.fixture(scope="session")
def mock_consumer():
    def _mock_consumer(mock_broker, topics, group_id, start_at=StartPosition.EARLIEST):
        class ConsumerBrokerWrapper:
            def __init__(self, broker, topics, group_id, start_at):
                if isinstance(topics, str):
                    topics = [topics]
                self.broker = broker
                self.topics = topics
                self.group_id = group_id
                self.start_at = start_at

            def subscribe(self, topics):
                for topic in topics:
                    assert topic in set(self.topics)

            def stream(self, *args, **kwargs):
                class Message:
                    def __init__(self, value, headers=[]):
                        self._value = value
                        self._headers = headers

                    def value(self):
                        return self._value

                    def headers(self):
                        return self._headers

                for message in self.broker.read(self.topics, self.group_id, self.start_at, **kwargs):
                    yield Message(message[0], message[1])

            def close(self):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                pass

        consumer = ConsumerBrokerWrapper(mock_broker, topics, group_id, start_at)
        return consumer

    return _mock_consumer


@pytest.fixture(scope="session")
def mock_kafka_message():
    message = MagicMock()
    message.topic.return_value = "test-topic"
    message.partition.return_value = 0
    message.offset.return_value = 0
    message.timestamp.return_value = (0, 1234567890)
    message.key.return_value = "test-key"
    message.headers.return_value = [("a header", "a value"), ("another header", "other value")]
    return message


@pytest.fixture(scope="session")
def legacy_auth_config():
    return AUTH_CONFIG_LEGACY


@pytest.fixture(scope="session")
def auth_config():
    return AUTH_CONFIG


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


@pytest.fixture(scope="session")
def voevent_fileobj():
    return io.BytesIO(VOEVENT_XML.encode())


@pytest.fixture(scope="session")
def voevent_text():
    return VOEVENT_XML


@pytest.fixture(scope="session")
def blob_text():
    return MESSAGE_BLOB


@pytest.fixture(scope="session")
def blob_msg():
    return {"content": MESSAGE_BLOB}


@pytest.fixture(scope="session")
def message_parameters_dict():
    # Generalize model_name, expected_model, test_file, and model_text
    # for easy access during tests. Useful when combined with parametrization
    # across message format, since fixtures (e.g., GCN_CIRCULAR) cannot be
    # used as parametrize arguments.
    return {
        "circular": {
            "model_name": "GCNCircular",
            "expected_model": models.GCNCircular,
            "test_file": "example_gcn.gcn3",
            "model_text": GCN_CIRCULAR,
        },
        "voevent": {
            "model_name": "VOEvent",
            "expected_model": models.VOEvent,
            "test_file": "example_voevent.xml",
            "model_text": VOEVENT_XML.encode(),
        },
        "blob": {
            "model_name": "Blob",
            "expected_model": str,
            "test_file": "example_blob.txt",
            "model_text": MESSAGE_BLOB,
        },
    }


@contextmanager
def temp_environ(**vars):
    """
    A simple context manager for temporarily setting environment variables

    Kwargs:
        variables to be set and their values

    Returns:
        None
    """
    from os import environ
    original = dict(environ)
    os.environ.update(vars)
    try:
        yield  # no value needed
    finally:
        # restore original data
        os.environ.clear()
        os.environ.update(original)


@contextmanager
def temp_config(tmpdir, data, perms=stat.S_IRUSR | stat.S_IWUSR):
    """
    A context manager which creates a temporary config file with specified data and permissions

    Args:
        data: the data to be written to the file
        perms: the permissions which should be set on the file.
            The default value is to use the standard, safe permissions

    Returns:
        The path to the config directory for hop to use this config file, as a string
    """

    config_path = f"{tmpdir}/hop/auth.toml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    config_file = open(config_path, mode='w')
    os.chmod(config_path, perms)
    config_file.write(data)
    config_file.close()
    try:
        yield str(tmpdir)
    finally:
        # remove file
        os.remove(config_path)
