# phantomnet_agent/pyinstaller/agent-linux.spec

import os
import sys

# Get the base directory of the project
project_root = os.path.abspath(os.path.join(SPECPATH, '..', '..'))
agent_dir = os.path.join(project_root, 'phantomnet_agent')
venv_lib_path = os.path.join(project_root, '.venv_phantomnet', 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages')

# Add the venv site-packages to the path for PyInstaller to find modules
sys.path.append(venv_lib_path)

block_cipher = None

a = Analysis(
    [os.path.join(agent_dir, 'main.py')],
    pathex=[project_root],  # Search for modules in the project root
    binaries=[],
    datas=[
        (os.path.join(agent_dir, 'config'), 'phantomnet_agent/config'),
        (os.path.join(agent_dir, 'schemas'), 'phantomnet_agent/schemas'),
        (os.path.join(agent_dir, 'certs'), 'phantomnet_agent/certs'),
        (os.path.join(agent_dir, 'platform_compatibility'), 'phantomnet_agent/platform_compatibility'),
        (os.path.join(agent_dir, 'collectors'), 'phantomnet_agent/collectors'),
        (os.path.join(agent_dir, 'actions'), 'phantomnet_agent/actions'),
        (os.path.join(agent_dir, 'bus'), 'phantomnet_agent/bus'),
        (os.path.join(agent_dir, 'core'), 'phantomnet_agent/core'),
        (os.path.join(agent_dir, 'api'), 'phantomnet_agent/api'),
        (os.path.join(agent_dir, 'security'), 'phantomnet_agent/security'),
        (os.path.join(agent_dir, 'shared'), 'phantomnet_agent/shared'),
        (os.path.join(agent_dir, 'log_forwarder.py'), 'phantomnet_agent/log_forwarder.py'),
        (os.path.join(agent_dir, 'orchestrator.py'), 'phantomnet_agent/orchestrator.py'),
        (os.path.join(agent_dir, 'telemetry_collector.py'), 'phantomnet_agent/telemetry_collector.py'),
        (os.path.join(agent_dir, 'generate_certs.py'), 'phantomnet_agent/generate_certs.py'),
        (os.path.join(agent_dir, 'self_healing_infrastructure.py'), 'phantomnet_agent/self_healing_infrastructure.py'),
        # Add any other top-level Python files or directories needed by the agent
    ],
    hiddenimports=[
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.quic.auto',
        'asyncio',
        'httpx'
        # Add any other modules that PyInstaller might miss
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter', 'PyQt5', 'PyQt4', 'wxPython', 'PySide', # GUI frameworks
        'numpy', 'pandas', 'scipy', 'matplotlib', 'tensorflow', 'torch', # Heavy data science libraries
        'IPython', 'jupyter', 'notebook', # Development tools
        'test', 'pytest', 'unittest', # Testing frameworks
        'setuptools', 'distutils', # Packaging tools
        'http.server', 'xml', 'email', # Often not needed in deployed agents
        'paramiko', 'fabric', # SSH clients (unless specifically needed)
        'pydoc', 'asyncio.proactor_events', 'asyncio.windows_events', # Windows-specific for Linux build
        # Exclude platform-specific adapters not for this OS if we were building universal
        # For Linux, exclude windows_adapter, termux_adapter from direct inclusion if possible
        'phantomnet_agent.platform_compatibility.windows_adapter',
        'phantomnet_agent.platform_compatibility.termux_adapter'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='phantomnet-agent',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_info=None,
          console=True,  # Agent usually runs in console/service mode
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
