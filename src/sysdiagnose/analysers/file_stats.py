import os
import magic
from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser
from sysdiagnose.utils.base import BaseAnalyserInterface, logger

class FileStatisticsAnalyser(BaseAnalyserInterface):
    description = "Obatins statistics about the files of the sysdiagnose"
    format = "json"  # Output format

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_file_type(self, file_path: str) -> str:
        return magic.from_file(file_path, mime=True)

    def traverse_directory(self, directory: str) -> dict:
        sysdiagnose_stats = []
        for root, dirs, files in os.walk(directory):
            directory_info = {
                "folder_name": os.path.relpath(root, start=directory),
                "file_count": len(files),
                "files": []
            }

            for file in files:
                file_path = os.path.join(root, file)
                file_info = {
                    "filename": file,
                    "extension": os.path.splitext(file)[1],
                    "file_type": self.get_file_type(file_path)
                }
                directory_info["files"].append(file_info)

            sysdiagnose_stats.append(directory_info)

        return sysdiagnose_stats

    def execute(self) -> dict:
        result = []
        rctl_parser = RemotectlDumpstateParser(self.config, self.case_id)
        rctl_result = rctl_parser.get_result()
        # device info
        device_info = {}
        try:
            device_info = {
                "os_version": rctl_result['Local device']['Properties']['OSVersion'],
                "build": rctl_result['Local device']['Properties']['BuildVersion'],
                "product_name": rctl_result['Local device']['Properties']['ProductName'],
                "product_type": rctl_result['Local device']['Properties']['ProductType']
            }
        except KeyError:
            logger.exception("Issue extracting device info")
        result.append(device_info)

        directory_path = self.case_data_subfolder
        result.append(self.traverse_directory(directory_path))

        return result
