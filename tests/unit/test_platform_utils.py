# tests/unit/test_platform_utils.py

import pytest
import os
import sys
import shutil
from unittest.mock import patch, MagicMock
from shared.platform_utils import (
    _detect_os_type,
    _is_root_user,
    _check_command_exists,
    _detect_system_capabilities,
    get_platform_details,
    OS_WINDOWS, OS_LINUX, OS_UNKNOWN,
    IS_WINDOWS, IS_LINUX, IS_ROOT,
    HAS_EBPF, HAS_PCAP, CAN_BIND_LOW_PORTS, SAFE_MODE,
)

@pytest.fixture(autouse=True)
def reset_platform_info():
    """Resets global state of platform_utils before each test."""
    original_is_windows = IS_WINDOWS
    original_is_linux = IS_LINUX
    original_is_root = IS_ROOT
    original_has_ebpf = HAS_EBPF
    original_has_pcap = HAS_PCAP
    original_can_bind_low_ports = CAN_BIND_LOW_PORTS
    original_safe_mode = SAFE_MODE

    # Clear previously set values
    with patch('shared.platform_utils.CURRENT_OS_TYPE', OS_UNKNOWN), \
         patch('shared.platform_utils.IS_WINDOWS', False), \
         patch('shared.platform_utils.IS_LINUX', False), \
         patch('shared.platform_utils.IS_ROOT', False), \
         patch('shared.platform_utils.HAS_EBPF', False), \
         patch('shared.platform_utils.HAS_PCAP', False), \
         patch('shared.platform_utils.CAN_BIND_LOW_PORTS', False), \
         patch('shared.platform_utils.SAFE_MODE', False), \
         patch('shared.platform_utils.PLATFORM_INFO', {}):
        yield
    
    # Restore original values
    with patch('shared.platform_utils.IS_WINDOWS', original_is_windows), \
         patch('shared.platform_utils.IS_LINUX', original_is_linux), \
         patch('shared.platform_utils.IS_ROOT', original_is_root), \
         patch('shared.platform_utils.HAS_EBPF', original_has_ebpf), \
         patch('shared.platform_utils.HAS_PCAP', original_has_pcap), \
         patch('shared.platform_utils.CAN_BIND_LOW_PORTS', original_can_bind_low_ports), \
         patch('shared.platform_utils.SAFE_MODE', original_safe_mode):
        pass


class TestPlatformUtils:

    @patch('os.name', 'posix')
    @patch('platform.system', MagicMock(return_value='Linux'))
    @patch.dict(os.environ, {}, clear=True)
    def test_detect_os_type_linux(self):
        assert _detect_os_type() == OS_LINUX

    @patch('os.name', 'nt')
    def test_detect_os_type_windows(self):
        assert _detect_os_type() == OS_WINDOWS

    @patch('os.name', 'posix')
    @patch('platform.system', MagicMock(return_value='Darwin'))
    def test_detect_os_type_unknown(self):
        assert _detect_os_type() == OS_UNKNOWN
    
    @patch('os.geteuid', MagicMock(return_value=0))
    @patch('shared.platform_utils.CURRENT_OS_TYPE', OS_LINUX)
    def test_is_root_user_linux(self):
        assert _is_root_user() == True

    @patch('os.geteuid', MagicMock(return_value=1000))
    @patch('shared.platform_utils.CURRENT_OS_TYPE', OS_LINUX)
    def test_is_not_root_user_linux(self):
        assert _is_root_user() == False
    
    @patch('shared.platform_utils.CURRENT_OS_TYPE', OS_WINDOWS)
    @patch('os.getuid', side_effect=AttributeError)
    def test_is_admin_user_windows(self, mock_getuid):
        mock_ctypes = MagicMock()
        mock_ctypes.windll.shell32.IsUserAnAdmin.return_value = 1
        with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
            assert _is_root_user() == True

    @patch('shared.platform_utils.CURRENT_OS_TYPE', OS_WINDOWS)
    @patch('os.getuid', side_effect=AttributeError)
    def test_is_not_admin_user_windows(self, mock_getuid):
        mock_ctypes = MagicMock()
        mock_ctypes.windll.shell32.IsUserAnAdmin.return_value = 0
        with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
            assert _is_root_user() == False

    @patch('shutil.which', MagicMock(return_value='/usr/bin/some_cmd'))
    def test_check_command_exists_true(self):
        assert _check_command_exists('some_cmd') == True

    @patch('shutil.which', MagicMock(return_value=None))
    def test_check_command_exists_false(self):
        assert _check_command_exists('non_existent_cmd') == False

    @patch('shared.platform_utils.CURRENT_OS_TYPE', OS_LINUX)
    @patch('shared.platform_utils.IS_ROOT', True)
    @patch('shared.platform_utils._check_command_exists', side_effect=lambda x: x in ['systemctl', 'bpftool', 'libpcap'])
    def test_detect_system_capabilities_linux_root(self, mock_check):
        caps = _detect_system_capabilities()
        assert caps['os_type'] == OS_LINUX
        assert caps['is_root'] == True
        assert caps['has_systemctl'] == True
        assert caps['has_ebpf'] == True
        assert caps['has_pcap'] == True
        assert caps['can_bind_low_ports'] == True
        assert caps['supports_raw_sockets'] == True

    @patch('shared.platform_utils.CURRENT_OS_TYPE', OS_WINDOWS)
    @patch('shared.platform_utils.IS_ROOT', True)
    @patch('shared.platform_utils._check_command_exists', side_effect=lambda x: x in ['sc.exe'])
    def test_detect_system_capabilities_windows_admin(self, mock_check):
        with patch('shared.platform_utils.wmi', create=True), \
             patch('shared.platform_utils.win32serviceutil', create=True):
            caps = _detect_system_capabilities()
            assert caps['os_type'] == OS_WINDOWS
            assert caps['is_root'] == True
            assert caps['has_sc_exe'] == True
            assert caps['has_npcap'] == True
            assert caps['can_bind_low_ports'] == True
            assert caps['supports_raw_sockets'] == True

    @patch.dict(os.environ, {'PHANTOMNET_SAFE_MODE': 'true'}, clear=True)
    def test_safe_mode_env_override(self):
        from importlib import reload
        reload(sys.modules['shared.platform_utils'])
        assert sys.modules['shared.platform_utils'].SAFE_MODE == True
        del os.environ['PHANTOMNET_SAFE_MODE']
        reload(sys.modules['shared.platform_utils'])
        assert sys.modules['shared.platform_utils'].SAFE_MODE == False

    @patch('shared.platform_utils.PLATFORM_INFO', {
        "os_type": OS_LINUX, "is_root": True, "has_ebpf": True, "has_pcap": True,
        "can_bind_low_ports": True, "supports_raw_sockets": True, "safe_mode": False
    })
    def test_get_platform_details(self):
        details = get_platform_details()
        assert details['os_type'] == OS_LINUX
        assert details['is_root'] == True
        assert details['has_ebpf'] == True
