# src/utils/path_helper.py
import os
import sys
from loguru import logger

def get_resource_path(relative_path):
    """
    [A1000] Universal Resource Resolver.
    For internal files bundled INSIDE the EXE.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.getcwd()
    
    return os.path.join(base_path, relative_path)

def get_external_resource(relative_path):
    """
    [A1000/A567] External Resource Resolver with ASCII Root Bridge.
    Sentencepiece/C++ legacy libs fail with non-ASCII paths (Error #42).
    This creates a root-level ASCII junction to bypass encoding issues.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.getcwd()
        
    long_path = os.path.abspath(os.path.join(base_path, relative_path))
    
    # If path is already pure ASCII, return as is
    if all(ord(c) < 128 for c in long_path):
        return long_path

    # [A567] ROOT BRIDGE: Gold standard for non-ASCII path survival
    if sys.platform == 'win32':
        return get_root_ascii_bridge(long_path)
    
    return long_path

def get_root_ascii_bridge(long_path):
    """
    [A567/A568/A570] Creates a junction at the root of a drive (e.g. C:\.aiv_bridge)
    Junctions are ASCII-safe and bypass Chinese characters in the middle of paths.
    """
    import subprocess
    import shutil
    import hashlib
    
    # [A570] Detect if drive is C: or other
    drive = os.path.splitdrive(long_path)[0] or "C:"
    
    # List of potential bridge roots to try
    # C:\ is best, but if drive D: is where the app is, D:\.aiv_bridge is also ASCII-safe!
    roots_to_try = ["C:\\.aiv_bridge", os.path.join(drive, "\\.aiv_bridge")]
    
    path_hash = hashlib.md5(long_path.encode('utf-8')).hexdigest()[:8]
    safe_name = f"link_{path_hash}"

    for bridge_root in roots_to_try:
        try:
            if not os.path.exists(bridge_root):
                os.makedirs(bridge_root, exist_ok=True)
            
            bridge_path = os.path.join(bridge_root, safe_name)
            
            # [A570] Use lexists to detect even broken junctions/links
            if os.path.lexists(bridge_path):
                # If it's a junction/directory, we assume it's valid for this hash
                # (since hash is unique to the long_path)
                return bridge_path
            
            # Attempt to create junction
            cmd = f'cmd /c mklink /J "{bridge_path}" "{long_path}"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if res.returncode == 0:
                logger.success(f"🌉 [A570] Bridge Success: {bridge_path} -> {long_path}")
                return bridge_path
            elif "當檔案已存在時" in res.stderr or "already exists" in res.stderr.lower():
                # [A570] If mklink complains it exists but lexists missed it (rare),
                # try one aggressive wipe and re-link.
                subprocess.run(f'cmd /c rmdir "{bridge_path}"', shell=True)
                res2 = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res2.returncode == 0:
                    return bridge_path
                    
        except Exception as e:
            logger.warning(f"🌉 [A570] Bridge Root {bridge_root} failed: {e}")
            continue

    # Final fallback to 8.3 short path if all bridges fail
    logger.error("🌉 [A570] All Root Bridges failed. Falling back to 8.3 short path.")
    return get_win32_short_path(long_path)

def get_win32_short_path(long_path):
    """
    [A566] Uses Win32 API to get the 8.3 short path name.
    This is the gold standard for bypassing non-ASCII path issues in legacy C++ libs.
    """
    import ctypes
    from ctypes import wintypes
    
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD
    
    # First call to get required buffer size
    output_buf_size = 0
    output_buf_size = _GetShortPathNameW(long_path, None, 0)
    if output_buf_size == 0:
        logger.error(f"❌ [A566] Failed to get short path for: {long_path}")
        return long_path
        
    output_buf = ctypes.create_unicode_buffer(output_buf_size)
    _GetShortPathNameW(long_path, output_buf, output_buf_size)
    short_path = output_buf.value
    logger.info(f"🌉 [A566] Path Bridge (8.3): {long_path} -> {short_path}")
    return short_path

def get_ascii_bridge_path(long_path):
    # Deprecated in favor of get_win32_short_path [A566]
    return get_win32_short_path(long_path)

def get_writable_path(relative_path):
    """
    [A670/A554] Persistent Data Resolver.
    Ensures user data lives next to the EXE or main script, not in CWD.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = os.path.dirname(sys.executable)
    else:
        # [A554] Get the directory of the main entry point to be absolute
        import __main__
        if hasattr(__main__, "__file__"):
            base_path = os.path.dirname(os.path.abspath(__main__.__file__))
        else:
            base_path = os.getcwd()
        
    target = os.path.join(base_path, relative_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    return target

def initialize_universal_environment():
    """
    [A1000] Global environment setup to be called at main start.
    """
    try:
        # Register embedded bin folder to system PATH immediately
        if hasattr(sys, '_MEIPASS'):
            bin_dir = os.path.join(sys._MEIPASS, "bin")
            if os.path.exists(bin_dir):
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]
                logger.success(f"🛡️ [A1000] Iron-Clad Binaries Locked: {bin_dir}")
                
        # Silence FFmpeg warnings by explicitly setting paths for pydub
        from pydub import AudioSegment
        ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        
        # Check dev vs prod path
        dev_ffmpeg = os.path.join(os.getcwd(), "bin", ffmpeg_name)
        prod_ffmpeg = os.path.join(getattr(sys, '_MEIPASS', os.getcwd()), "bin", ffmpeg_name)
        
        if os.path.exists(prod_ffmpeg):
            AudioSegment.converter = prod_ffmpeg
        elif os.path.exists(dev_ffmpeg):
            AudioSegment.converter = dev_ffmpeg
            
    except Exception as e:
        logger.warning(f"Environment initialization warning: {e}")
