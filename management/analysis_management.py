import json
from datetime import datetime
from glob import glob
from pathlib import Path

import bson
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt


class AnalysisManagement:
    def __init__(self, main_window):
        self.main_window = main_window
        self.ui = main_window.ui
        # Analyses List:
        self.ui.listAnalyses.setModel(QtGui.QStandardItemModel())
        self.ui.listAnalyses.clicked.connect(self.analysis_clicked)
        self.analysis_base_dir = self.main_window.CacheDir / "Analyses"
        self.analysis_base_dir.mkdir(exist_ok=True)
        self.files = {}
        self.populate_analyses_list()

        # Analyses buttons:
        self.ui.btn_new_analysis.setEnabled(False)
        self.ui.btn_new_analysis.clicked.connect(self.new_analysis)

        self.ui.btn_edit_analysis.clicked.connect(self.edit_analysis)
        self.ui.btn_edit_analysis.setEnabled(False)

        self.ui.btn_del_analysis.clicked.connect(self.delete_analysis)
        self.ui.btn_del_analysis.setEnabled(False)

        self.ui.btn_commit.clicked.connect(self.commit_analysis_to_instance)
        self.ui.btn_commit.setEnabled(False)

    def commit_analysis_to_instance(self):
        selection_model = self.ui.listAnalyses.selectionModel()
        model = self.ui.listAnalyses.model()
        item = model.itemFromIndex(selection_model.currentIndex())
        data = item.data()
        analysis_parent = self.main_window.fw_client.get(data["container_id"])
        output_dir = data["output"]
        input_files = []
        for k, v in data["input_files"].items():
            # resolve file reference
            input_path = Path(v)
            container = self.main_window.fw_client.get(
                str(input_path.parents[1]).split("/")[-1]
            )
            filename = input_path.name
            file_ref = container.get_file(filename).ref()
            # append to input_files object
            input_files.append(file_ref)

        anal = analysis_parent.add_analysis(
            label=data["analysis_name"], inputs=input_files
        )

        for path in glob(output_dir + "/*"):
            path = Path(path)
            if path.is_file():
                anal.upload_output(str(path))

    def populate_analyses_list(self):
        model = self.ui.listAnalyses.model()
        analyses = glob(str(self.analysis_base_dir / "*"))
        for analysis_dir in [Path(an) for an in analyses]:
            with open(str(analysis_dir / "config.json"), "r") as fp:
                analysis_config = json.load(fp)
                analysis_text = analysis_config["analysis_name"]
                item = QtGui.QStandardItem(analysis_text)
                item.setToolTip(analysis_text)
                item.setData(analysis_config)
                model.appendRow(item)

    def new_analysis(self):
        methods = ["Native_OS", "Docker_X11", "Docker_novnc"]
        method = methods[
            [
                self.ui.rdNative.isChecked(),
                self.ui.rdX11.isChecked(),
                self.ui.rdNovnc.isChecked(),
            ].index(True)
        ]

        model = self.ui.listAnalyses.model()
        item = self.ui.listApps.currentItem()
        app_text = item.text()
        analysis_text = app_text + ": " + str(datetime.now())
        analysis_dir = self.analysis_base_dir / str(bson.ObjectId())
        derived_dir = analysis_dir / "derived_files"
        derived_dir.mkdir(parents=True)

        analysis_config = {
            "analysis_name": analysis_text,
            "path": str(analysis_dir),
            "output": str(derived_dir),
            "container_id": self.main_window.tree_management.current_item.data(),
            "app_name": app_text,
            "os": self.main_window.app_management.platform,
            "method": method,
            "input_files": self.files,
            "project_file": None,
            "committed": None,
        }

        with open(analysis_dir / "config.json", "w") as fp:
            json.dump(analysis_config, fp, indent=4)

        item = QtGui.QStandardItem(analysis_text)
        item.setToolTip(analysis_text)
        item.setData(analysis_config)
        model.appendRow(item)
        self.ui.listAnalyses.setCurrentIndex(item.index())

    def analysis_clicked(self):
        self.set_controls_to_list()

    def set_controls_to_list(self):
        # Ensure that the controls are set to the proper app and method before launching
        selection_model = self.ui.listAnalyses.selectionModel()
        model = self.ui.listAnalyses.model()
        item = model.itemFromIndex(selection_model.currentIndex())
        data = item.data()

        self.ui.btn_edit_analysis.setEnabled(True)
        self.ui.btn_del_analysis.setEnabled(True)
        self.ui.btn_commit.setEnabled(True)

        # set radio value
        methods = ["Native_OS", "Docker_X11", "Docker_novnc"]
        radios = [self.ui.rdNative, self.ui.rdX11, self.ui.rdNovnc]
        radios[methods.index(data["method"])].setChecked(True)

        # set app list value
        item = self.ui.listApps.findItems(data["app_name"], Qt.MatchExactly)[0]
        self.ui.listApps.setCurrentItem(item)
        return data

    def edit_analysis(self):
        data = self.set_controls_to_list()
        self.main_window.tree_management.cache_selected_for_open()
        for k, v in self.files.items():
            data["input_files"][k] = v

        with open(data["path"] + "/config.json", "w") as fp:
            json.dump(data, fp, indent=4)
        self.main_window.app_management.launch_app(data)

    def delete_analysis(self):
        pass
