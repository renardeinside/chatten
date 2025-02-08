from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from pathlib import Path
import subprocess

class DashBuildHook(BuildHookInterface):
    def initialize(self, _, __):
        self.app.display_info(f"Running dash build hook for project {self.metadata.name} in directory {Path.cwd()}")
        
        process = subprocess.Popen(
            ['npm', 'run', 'build'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in process.stdout:
            self.app.display_info(line, end='')

        for line in process.stderr:
            self.app.display_error(line, end='')

        process.wait()

