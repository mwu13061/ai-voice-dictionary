# src/utils/module_loader.py
import os
import sys
import importlib.util
from loguru import logger
from src.utils.path_helper import get_resource_path # [A670]

class ModuleLoader:
    """ [A670] Dynamic Component Loader with EXE support """
    
    @staticmethod
    def _probe_path(relative_path):
        """ [A1000] Resilient path probing for frozen environments """
        candidates = []
        meipass = getattr(sys, '_MEIPASS', 'NOT_SET')
        exe_dir = os.path.dirname(sys.executable)
        cwd = os.getcwd()
        
        logger.debug(f"🔍 Probing for: {relative_path}")
        logger.debug(f"🔍 System Context: MEIPASS={meipass}, EXE_DIR={exe_dir}, CWD={cwd}")
        logger.debug(f"🔍 sys.path[0-2]: {sys.path[:3]}")

        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, relative_path))
            candidates.append(os.path.join(sys._MEIPASS, "_internal", relative_path))
            candidates.append(os.path.join(exe_dir, relative_path))
            candidates.append(os.path.join(exe_dir, "_internal", relative_path))
        else:
            candidates.append(os.path.join(cwd, relative_path))
            
        for p in candidates:
            exists = os.path.exists(p)
            logger.debug(f"   - Checking: {p} [{'FOUND' if exists else 'MISSING'}]")
            if exists:
                return p
        return None

    @staticmethod
    def load_engine(engine_version: str):
        try:
            import traceback
            logger.info(f"Loader Audit: Requesting engine version '{engine_version}'")
            if not engine_version:
                logger.error("Loader Error: engine_version is empty!")
                return None
                
            rel_path = os.path.join("src", "audio", "engines", f"engine_{engine_version}.py")
            file_path = ModuleLoader._probe_path(rel_path)
            
            if not file_path:
                logger.error(f"Loader Error: Engine file not found after probing: {rel_path}")
                return None
                
            logger.info(f"Loader Audit: Loading engine from {file_path}")
            spec = importlib.util.spec_from_file_location(f"engine_{engine_version}", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Map version string to class name
            class_map = {
                "v2_stable": "EngineV2Stable",
                "v1_legacy": "EngineV1Legacy"
            }
            class_name = class_map.get(engine_version, "EngineV2Stable")
            
            # [A379] VERBOSE LOAD TRACEBACK
            try:
                instance = getattr(module, class_name)()
                return instance
            except Exception as e:
                logger.critical(f"CRITICAL: Engine Instance Creation Failed!\n{traceback.format_exc()}")
                return None
                
        except Exception as e:
            import traceback
            logger.error(f"Engine Load Failed Traceback:\n{traceback.format_exc()}")
            return None

    @staticmethod
    def load_output_plugin(plugin_version: str):
        try:
            rel_path = os.path.join("src", "utils", "output_plugins", f"plugin_{plugin_version}.py")
            file_path = ModuleLoader._probe_path(rel_path)
            
            if not file_path: return None
                
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_version}", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            class_name = "OutputPlugin"
            return getattr(module, class_name)()
        except Exception as e:
            logger.error(f"Plugin Load Failed: {e}")
            return None
