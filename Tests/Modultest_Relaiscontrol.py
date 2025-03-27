import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from relaiscontrol import RelaisControl

def test_relais_toggle():
    relais = RelaisControl()
    
    assert relais.device is not None, "Fehler: Relais konnte nicht erfolgreich verbunden werden"
    
    try:
        for _ in range(1000):
            assert relais.on_all() == True, "Fehler: Relais konnte nicht eingeschaltet werden"
            assert relais.off_all() == True, "Fehler: Relais konnte nicht ausgeschaltet werden"
    finally:
        relais.close_device()
        assert relais.device is None, "Fehler: Relais konnte nicht erfolgreich geschlossen werden"
