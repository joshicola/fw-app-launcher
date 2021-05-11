import copy
import json
import os
import platform
import subprocess
import tempfile
import webbrowser
from glob import glob
from pathlib import Path

import docker
import ifcfg
import pystache

# TODO: Put this in "resources" and (eventually) a copy in ~/.config/flywheel/

apps_config = {
    "Slicer": {
        "Native_OS": {
            "Darwin": {
                "command": [
                    "/usr/bin/open",
                    "-W",
                    "-n",
                    "-a",
                    "/Applications/Slicer.app",
                ],
                "file_arg_prefix": "--args",
                "init_file": "resources/Slicer.ini",
                "init_file_path": "~/.config/www.na-mic.org/",
                "project_exts": ["mrb", "mrml"],
                "project_args": "--python-script {{path}}/run.py",
            },
            "Linux": {},
            "Windows": {},
        },
        "Docker_novnc": {
            "Darwin": {
                "command": [
                    "/usr/bin/open",
                    "-W",
                    "-n",
                    "-a",
                    "/Applications/Slicer.app",
                ],
                "docker-image": "stevepieper/slicer-chronicle:latest",
                "docker_kwargs": {
                    "volumes": {},
                    "environment": {},
                    "ports": {"8080": "8080"},
                    "name": "slicer",
                    "detach": True,
                },
                "project_exts": ["mrb", "mrml"],
            },
            "Linux": {},
            "Windows": {},
        },
    },
    "ITK-SNAP": {
        "Native_OS": {
            "Darwin": {
                "command": [
                    "/usr/bin/open",
                    "-W",
                    "-n",
                    "-a",
                    "/Applications/ITK-SNAP.app",
                ],
                "file_arg_prefix": "--args",
                "first_file_flag": "-g",
                "additional_files_flag": "-o",
            },
            "Linux": {},
            "Windows": {},
        }
    },
    "MRIcron": {
        "Native_OS": {
            "Darwin": {
                "command": [
                    "/usr/bin/open",
                    "-W",
                    "-n",
                    "-a",
                    "/Applications/MRIcron.app",
                ],
                "file_arg_prefix": "--args",
            },
            "Linux": {},
            "Windows": {},
        }
    },
    "ImageJ": {
        "Native_OS": {
            "Darwin": {
                "command": [
                    "/usr/bin/open",
                    "-W",
                    "-n",
                    "-a",
                    "/Applications/ImageJ.app",
                ],
            },
            "Linux": {},
            "Windows": {},
        }
    },
}


class AppManagement:
    """
    Class that coordinates all app-related functionality.
    """

    def __init__(self, main_window):
        """
        Initializes and populates all app-related components.

        Args:
            main_window (AppLauncher): Component-initialized main window.
        """
        self.main_window = main_window
        self.ui = main_window.ui
        self.platform = platform.system()

        # Initialize ui components
        if self.platform == "Darwin":
            message = "Available on OS X:"
        elif self.platform == "Linux":
            message = "Available on Linux:"
        elif self.platform == "Windows":
            message = "Available on Windows:"
        else:
            message = "System is unknown."

        self.ui.lbl_platform.setText(message)

        self.ui.btnLaunchApp.clicked.connect(self.view_in_app)
        # TODO: How do I compensate for the "drag select"?
        self.ui.listApps.itemSelectionChanged.connect(self.app_list_change)

        self.ui.listApps.setCurrentItem(self.ui.listApps.item(0))

        # self.ui.rdNative.setChecked(False)

        self.fill_app_list()
        self.tmpdir = tempfile.TemporaryDirectory()

    def fill_app_list(self):
        """
        Fill app list view with apps that are locally available.

        Locally available entails:
            * There is an executable on the system
            * There is a docker image that supports x11 or novnc interaction
        """
        # TODO: Change applist to QListView to accept data objects
        # TODO: List app only if it has a valid launcher.... Or "Dim"
        for k, v in apps_config.items():
            self.ui.listApps.addItem(k)  # item)
            # item = self.ui.listApps.item(self.ui.listApps.count() - 1)
            # item.setData(0, {"Hi": "No"})
            # item.setData(1, {"Hi": "No"})
            # item.setData(2, {"Hi": "No"})
            # item.setHidden(True)
            # for i, method in enumerate(["Native_OS", "Docker_X11", "Docker_novnc"]):
            #     if v.get(method):
            #         item.setData(i, v[method])
            #     else:
            #         item.setData(i, None)
            #     item.setHidden(False)

    def app_list_change(self):
        """
        On selecting a new app from list, adjust radio buttons to available methods.
        """
        item = self.ui.listApps.currentItem()
        app_text = item.text()
        methods = ["Native_OS", "Docker_X11", "Docker_novnc"]
        radio_buttons = [self.ui.rdNative, self.ui.rdX11, self.ui.rdNovnc]
        for i, radio_button in enumerate(radio_buttons):
            data = apps_config[app_text].get(methods[i])
            enabled = True

            if not data:
                enabled = False
                radio_button.setChecked(False)
            else:
                if i == 0:
                    enabled = Path(data[self.platform]["command"][-1]).exists()
                elif i == 1:
                    enabled = False
                elif i == 2:
                    enabled = data[self.platform]["docker-image"] in [
                        img.tags[0]
                        for img in docker.from_env().images.list()
                        if img.tags
                    ]
            radio_button.setEnabled(enabled)
        enabled_buttons = [rdo for rdo in radio_buttons if rdo.isEnabled()]
        if enabled_buttons:
            enabled_buttons[0].setChecked(True)

    def view_in_app(self):
        """
        Launch app with what files are selected in the tree view.
        """
        self.main_window.tree_management.cache_selected_for_open()
        app_data = {"input_files": self.main_window.tree_management.cache_files}
        self.launch_app(app_data)

    def launch_app(self, app_data):
        """
        Launch app with indicated data from tree or local analysis.

        Args:
            app_data (dict): A dictionary referencing selected files from tree or
                local analysis.
        """
        item = self.ui.listApps.currentItem()
        if item:
            app_text = item.text()
            if self.ui.rdNative.isChecked():
                self.launch_native(apps_config[app_text]["Native_OS"], app_data)
            elif self.ui.rdX11.isChecked():
                self.launch_x11(apps_config[app_text]["Docker_X11"], app_data)
            elif self.ui.rdNovnc.isChecked():
                self.launch_novnc(apps_config[app_text]["Docker_novnc"], app_data)

    def launch_native(self, app_def_native, app_data):
        """
        Launch an application on a native operating system (osx, linux, windows).

        Args:
            app_def_native (dict): A dictionary containing app-specific launch
                configuration.
            app_data (dict): A dictionary referencing selected files from tree or
                local analysis.
        """
        os_platform = platform.system()
        app_def_platform = copy.deepcopy(app_def_native[os_platform])
        command = app_def_platform["command"]
        # init_file may need to be managed....differently
        # Slicer.ini has user-specific paths....
        if app_def_platform.get("init_file"):
            init_file_template = (
                self.main_window.source_dir / app_def_platform["init_file"]
            )
            init_file_dir = Path(
                app_def_platform["init_file_path"].replace("~", os.path.expanduser("~"))
            )
            renderer = pystache.Renderer()
            original_init = init_file_dir / init_file_template.name
            original_init.rename(init_file_dir / (init_file_template.name + ".bak"))

        if app_data.get("output"):
            extensions = [
                glob(app_data["output"] + "/*." + ext)
                for ext in app_def_platform["project_exts"]
            ]
        else:
            app_data["output"] = os.path.expanduser("~")
            extensions = [[]]

        if app_def_platform.get("init_file"):
            template_output = renderer.render_path(init_file_template, app_data)

            with open(original_init, "w") as fp:
                fp.write(template_output)

        # TODO: How do I want to add new files to an existing project in Slicer
        #       For now, I don't.
        # TODO: using the .slicerrc.py in the ~/ loads what I need. But, if I want to
        #       load additional files....????
        #       currently, it loads twice the files I need. 1 from the project and one
        #       from the "input_files"...how do I load ones that ARE NOT IN the mrml?
        # if any(extensions):
        #     project_file = [fl[0] for fl in extensions if fl][0]
        #     command.append(app_def_platform["file_arg_prefix"])
        #     template_output = renderer.render(app_def_platform["project_args"], app_data)
        #     command.append(template_output)
        # else:
        if app_data["input_files"]:
            if app_def_platform.get("file_arg_prefix"):
                command.append(app_def_platform["file_arg_prefix"])
            for i, (_, v) in enumerate(app_data["input_files"].items()):
                if i == 0 and app_def_platform.get("first_file_flag"):
                    command.append(app_def_platform.get("first_file_flag"))
                elif i == 1 and app_def_platform.get("additional_files_flag"):
                    command.append(app_def_platform.get("additional_files_flag"))
                command.append(v)

        self.ui.btnLaunchApp.setEnabled(False)
        results = subprocess.run(command)
        self.ui.btnLaunchApp.setEnabled(True)

    def launch_x11(self, app_def_x11, app_data):
        """
        Launch an application with an x11 window from within docker container.

        This will not work on OS X due to discontinued nvidia drivers.

        Args:
            app_def_x11 (dict): A dictionary containing app-specific launch
                configuration.
            app_data (dict): A dictionary referencing selected files from tree or
                local analysis.
        """
        # command = "#!/bin/bash\n"
        # command += "itksnap"  # "/Fiji.app/ImageJ-linux64"
        # for i, (k, v) in enumerate(files.items()):
        #     command += (
        #         ' "' + v.replace("/Users/joshuajacobs/", "/home/researcher/") + '"'
        #     )
        ifcfg.interfaces()["en0"]["inet"]
        # with open(self.CacheDir / "run.sh", "w") as fp:
        #     fp.write(command)
        # os.chmod(self.CacheDir / "run.sh", 457)
        # ip = "10.53.1.140"
        # env = {
        #     "DISPLAY": f"{ip}:0",
        #     "SLICER_ARGUMENTS": " ".join(
        #         [
        #             v.replace("/Users/joshuajacobs/", "/home/researcher/")
        #             for k, v in files.items()
        #         ]
        #     ),
        # }
        # mounts = {
        #     "/Users/joshuajacobs/flywheelIO": {
        #         "bind": "/home/researcher/flywheelIO/",
        #         "mode": "ro",
        #     }
        # }
        # docker_kwargs = {
        #     "volumes": mounts,
        #     "environment": env,
        #     "ports": {"8080": "8080"},
        #     "name": "slicer",
        #     "detach": True,
        # }
        client = docker.from_env()
        container = client.containers.run(
            "stevepieper/slicer-chronicle",  # **docker_kwargs
        )

    def launch_novnc(self, app_def_novnc, app_data):
        """
        Launch dockerized application in a novnc web interface.

        Args:
            app_def_novnc (dict): A dictionary containing app-specific launch
                configuration.
            app_data (dict): A dictionary referencing selected files from tree or
                local analysis.
        """
        os_platform = platform.system()
        app_def_platform = copy.deepcopy(app_def_novnc[os_platform])
        if app_data.get("output"):
            extensions = [
                glob(app_data["output"] + "/*." + ext)
                for ext in app_def_platform["project_exts"]
            ]
        else:
            extensions = [[]]
        if any(extensions):
            files = [fl[0] for fl in extensions if fl]
            env = {
                "SLICER_ARGUMENTS": (
                    "--python-code \"slicer.util.loadScene('"
                    + files[0].replace("/Users/joshuajacobs/", "/home/researcher/")
                    + "')\""
                )
            }
        else:
            files = [
                v.replace("/Users/joshuajacobs/", "/home/researcher/")
                for k, v in app_data["input_files"].items()
            ]
            env = {
                "SLICER_ARGUMENTS": " ".join(files),
            }
        self.tmpdir.cleanup()
        self.tmpdir = tempfile.TemporaryDirectory()
        if app_data.get("output"):
            output_dir = app_data["output"]
            mode = "rw"
        else:
            output_dir = self.tmpdir.name
            mode = "ro"
        mounts = {
            str(self.main_window.CacheDir): {
                "bind": "/home/researcher/flywheelIO/",
                "mode": "ro",
            },
            # output_dir: {"bind": "/home/researcher/Documents", "mode": mode},
        }

        docker_kwargs = copy.deepcopy(app_def_platform["docker_kwargs"])
        docker_kwargs["volumes"] = mounts
        docker_kwargs["environment"] = env

        client = docker.from_env()
        # TODO: If the container is running, send the app_data rather than relaunching.
        #     : give the user an option to shut it down.
        try:
            container = client.containers.get(docker_kwargs["name"])
            container.kill()
            client.containers.prune()
        except Exception as e:
            print(e)

        container = client.containers.run(
            app_def_platform["docker-image"], **docker_kwargs
        )
        webbrowser.open(
            "http://localhost:8080/x11/vnc.html?autoconnect=true&path=x11/websockify"
        )
