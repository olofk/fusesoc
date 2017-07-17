import pytest

from fusesoc.vlnv import Vlnv

def vlnv_tuple(vlnv):
    return (vlnv.vendor, vlnv.library, vlnv.name, vlnv.version, vlnv.revision)

#VLNV tests without revision
def test_full_vlnv():
    assert vlnv_tuple(Vlnv("librecores.org:peripherals:uart16550:1.5")) == \
    ('librecores.org', 'peripherals', 'uart16550', '1.5', 0)

def test_full_vlnv_no_version():
    assert vlnv_tuple(Vlnv("librecores.org:peripherals:uart16550")) == \
    ('librecores.org', 'peripherals', 'uart16550', '0', 0)

def test_name_only_vlnv():
    assert vlnv_tuple(Vlnv("::uart16550")) == \
    ('', '', 'uart16550', '0', 0)
    assert vlnv_tuple(Vlnv("::uart16550:")) == \
    ('', '', 'uart16550', '0', 0)
    
def test_name_version_vlnv():
    assert vlnv_tuple(Vlnv("::uart16550:1.5")) == \
    ('', '', 'uart16550', '1.5', 0)

#VLNV tests with revision
def test_full_vlnv_revision():
    assert vlnv_tuple(Vlnv("librecores.org:peripherals:uart16550:1.5-r5")) == \
    ('librecores.org', 'peripherals', 'uart16550', '1.5', 5)

def test_name_only_vlnv_revision():
    assert vlnv_tuple(Vlnv("::uart16550")) == \
    ('', '', 'uart16550', '0', 0)
    assert vlnv_tuple(Vlnv("::uart16550:")) == \
    ('', '', 'uart16550', '0', 0)
    
def test_name_version_vlnv():
    assert vlnv_tuple(Vlnv("::uart16550:1.5")) == \
    ('', '', 'uart16550', '1.5', 0)

#Tests for legacy naming scheme
def test_name_version_legacy():
    assert vlnv_tuple(Vlnv("uart16550-1.5")) == \
    ('', '', 'uart16550', '1.5', 0)

def test_name_with_dash_version_legacy():
    assert vlnv_tuple(Vlnv("wb-axi-1.5")) == \
    ('', '', 'wb-axi', '1.5', 0)

def test_name_only_legacy():
    assert vlnv_tuple(Vlnv("uart16550")) == \
    ('', '', 'uart16550', '0', 0)

def test_name_with_dash_only_legacy():
    assert vlnv_tuple(Vlnv("wb-axi")) == \
    ('', '', 'wb-axi', '0', 0)

def test_name_version_revision_legacy():
    assert vlnv_tuple(Vlnv("uart16550-1.5-r2")) == \
    ('', '', 'uart16550', '1.5', 2)

def test_name_revision_legacy():
    assert vlnv_tuple(Vlnv("uart16550-r2")) == \
    ('', '', 'uart16550', '0', 2)

