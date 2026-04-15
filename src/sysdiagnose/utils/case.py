import json
import os
import shutil
import re
from sysdiagnose.utils.lock import FileLock
from sysdiagnose.utils.base import SysdiagnoseConfig

class SysdiagnoseCase:
    """
    Represent a sysdiagnose case.
    """
    def __init__(self, case_id: str, tags: list[str] = None, case_metadata: dict = None):
        # only allow specific chars for case_id
        if case_id:
            if not re.match(r'^[a-zA-Z0-9-_\.]+$', case_id):
                raise ValueError("Invalid case ID. Only alphanumeric and -_. characters are allowed.")
            
        self.case_id = case_id
        self.tags = tags if tags else []
        self.case_metadata = case_metadata if case_metadata else {}
        return
    
    def updateCaseMetadata(self, new_metadata: dict):
        self.case_metadata = new_metadata

    def getCaseMetadata(self) -> dict:
        return self.case_metadata
    

class SysdiagnoseCaseLibrary:
    """
    Represent a library of sysdiagnose cases.
    """
    def __init__(self, config: SysdiagnoseConfig):
        self.config = config
        self._cases = {}
        self.load_from_disk()
    
    def add_case(self, case: SysdiagnoseCase, force: bool = False) -> None:
        # check if sysdiagnose file is not already in a case
        for existing_case in self._cases.values():
            if existing_case.case_metadata.get('source_sha256') == case.case_metadata.get('source_sha256'):
                if force:
                    if existing_case.case_id != case.case_id:
                        raise ValueError(f"This sysdiagnose has already been extracted with different case ID: existing = {existing_case.case_id}, given = {case.case_id}")
                    # Update existing case
                    self._cases[case.case_id] = case
                    self.save_to_disk()
                    return
                else:
                    raise ValueError(f"This sysdiagnose has already been extracted for case ID: {existing_case.case_id}")
        
        # check if case_id already exists with different file
        if case.case_id in self._cases:
            existing_sha256 = self._cases[case.case_id].case_metadata.get('source_sha256')
            if existing_sha256 != case.case_metadata.get('source_sha256'):
                raise ValueError(f"Case ID {case.case_id} already exists but with a different sysdiagnose file.")

        # add new case
        self._cases[case.case_id] = case
        self.save_to_disk()

    def delete_case(self, case_id: str) -> None:
        if case_id in self._cases:
            self._cases.pop(case_id, None)
            case_folder = os.path.join(self.config.cases_root_folder, case_id)
            if os.path.isdir(case_folder):
                try:
                    shutil.rmtree(case_folder)
                except Exception as e:
                    raise Exception(f"Error while deleting case folder: {str(e)}")
            self.save_to_disk()
    
    def update_case(self, case_id: str, new_metadata: dict):
        if case_id in self._cases:
            self._cases[case_id].updateCaseMetadata(new_metadata)
            self.save_to_disk()

    def get_cases(self) -> dict:
        return self._cases
    
    def get_case(self, case_id: str) -> SysdiagnoseCase:
        return self._cases.get(case_id)
    
    def case_exists(self, case_id: str) -> bool:
        return case_id in self._cases
    
    def get_next_case_id(self) -> str:
        """Generate next incremental case ID"""
        case_id = 0
        for k in self._cases.keys():
            try:
                case_id = max(case_id, int(k))
            except ValueError:
                pass
        return str(case_id + 1)

    def reload(self):
        """
        Force reload the case library from disk.
        """
        self.load_from_disk()

    def save_to_disk(self) -> bool:
        """Save cases to disk, converting SysdiagnoseCase objects to dict format"""
        lock = FileLock(self.config.cases_file)
        try:
            lock.acquire()
            # Convert SysdiagnoseCase objects to dict format for JSON serialization
            cases_dict = {}
            for case_id, case in self._cases.items():
                case_data = case.case_metadata.copy()
                case_data['case_id'] = case.case_id
                case_data['tags'] = case.tags
                cases_dict[case_id] = case_data
            
            with open(self.config.cases_file, 'w') as f:
                json.dump(cases_dict, f, indent=4, sort_keys=True)
            return True
        except Exception as e:
            raise Exception(f"Error while saving case library to disk: {str(e)}")
        finally:
            lock.release()
        return False

    def load_from_disk(self) -> None:
        """Load cases from disk, converting dict format to SysdiagnoseCase objects"""
        if not os.path.exists(self.config.cases_file):
            self._cases = {}
            return  # No cases file yet, start with empty library
            
        lock = FileLock(self.config.cases_file)
        try:
            lock.acquire()
            with open(self.config.cases_file, 'r') as f:
                cases_dict = json.load(f)
            
            # Convert dict format to SysdiagnoseCase objects
            self._cases = {}
            for case_id, case_data in cases_dict.items():
                tags = case_data.pop('tags', [])
                case_metadata = case_data.copy()
                case = SysdiagnoseCase(case_id=case_id, tags=tags, case_metadata=case_metadata)
                self._cases[case_id] = case
        except Exception as e:
            raise Exception(f"Error while loading case library from disk: {str(e)}")
        finally:
            lock.release()
                    