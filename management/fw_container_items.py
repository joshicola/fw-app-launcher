import os
from pathlib import Path

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView


class ContainerItem(QtGui.QStandardItem):
    def __init__(self, parent_item, container):
        super(ContainerItem, self).__init__()
        self.has_analyses = False
        self.parent_item = parent_item
        self.container = container
        self.source_dir = Path(os.path.realpath(__file__)).parents[1]
        title = container.label
        self.setData(container.id)
        self.setText(title)
        self._set_icon()
        self.parent_item.appendRow(self)
        self._files_folder()
        self._analyses_folder()
        self._child_container_folder()

    def _set_icon(self):
        icon = QtGui.QIcon(str(self.source_dir / self.icon_path))
        self.setIcon(icon)

    def _files_folder(self):
        if hasattr(self.container, "files"):
            icon_path = "resources/folder.png"
            icon = QtGui.QIcon(str(self.source_dir / icon_path))

            self.filesItem = QtGui.QStandardItem()
            self.filesItem.setText("FILES")
            self.filesItem.setIcon(icon)
            self.appendRow(self.filesItem)

    def _list_files(self):
        if hasattr(self.container, "files"):
            if not self.filesItem.hasChildren() and self.container.files:
                for fl in self.container.files:
                    FileItem(self.filesItem, fl)

    def _analyses_folder(self):
        if hasattr(self.container, "analyses"):
            icon_path = "resources/folder.png"
            icon = QtGui.QIcon(str(self.source_dir / icon_path))
            self.analysesItem = QtGui.QStandardItem()
            self.analysesItem.setText("ANALYSES")
            self.analysesItem.setIcon(icon)
            self.appendRow(self.analysesItem)

    def _list_analyses(self):
        if hasattr(self.container, "analyses"):
            # self.container = self.container.reload()
            if not self.analysesItem.hasChildren() and self.container.analyses:
                for analysis in self.container.analyses[:10]:
                    AnalysisItem(self.analysesItem, analysis)

    def _child_container_folder(self):
        if hasattr(self, "child_container_name"):
            self.titleItem = QtGui.QStandardItem()
            self.titleItem.setText(self.child_container_name)
            icon_path = "resources/folder.png"
            icon = QtGui.QIcon(str(self.source_dir / icon_path))
            self.titleItem.setIcon(icon)
            self.appendRow(self.titleItem)

    def _on_expand(self):
        self._list_files()
        self._list_analyses()


class GroupItem(ContainerItem):
    def __init__(self, parent_item, group):
        self.icon_path = "resources/group.png"
        self.child_container_name = "PROJECTS"
        self.group = group
        super(GroupItem, self).__init__(parent_item, group)

    def _list_projects(self):
        if not self.titleItem.hasChildren():
            for project in self.group.projects():
                ProjectItem(self.titleItem, project)

    def _on_expand(self):
        super(GroupItem, self)._on_expand()
        self._list_projects()


class ProjectItem(ContainerItem):
    def __init__(self, group_item, project):
        self.icon_path = "resources/project.png"
        self.child_container_name = "SUBJECTS"
        super(ProjectItem, self).__init__(group_item, project)
        self.has_analyses = True
        self.project = self.container

    def _list_subjects(self):
        if not self.titleItem.hasChildren():
            for subject in self.project.subjects():
                SubjectItem(self.titleItem, subject)

    def _on_expand(self):
        super(ProjectItem, self)._on_expand()
        self._list_subjects()


class SubjectItem(ContainerItem):
    def __init__(self, project_item, subject):
        self.icon_path = "resources/subject.png"
        self.child_container_name = "SESSIONS"
        super(SubjectItem, self).__init__(project_item, subject)
        self.has_analyses = True
        self.subject = self.container

    def _list_sessions(self):
        if not self.titleItem.hasChildren():
            for session in self.subject.sessions():
                SessionItem(self.titleItem, session)

    def _on_expand(self):
        super(SubjectItem, self)._on_expand()
        self._list_sessions()


class SessionItem(ContainerItem):
    def __init__(self, project_item, session):
        self.icon_path = "resources/session.png"
        self.child_container_name = "ACQUISITIONS"
        super(SessionItem, self).__init__(project_item, session)
        self.has_analyses = True
        self.session = self.container

    def _list_acquisitions(self):
        if not self.titleItem.hasChildren():
            for acquisition in self.session.acquisitions():
                AcquisitionItem(self.titleItem, acquisition)

    def _on_expand(self):
        super(SessionItem, self)._on_expand()
        self._list_acquisitions()


class AcquisitionItem(ContainerItem):
    def __init__(self, session_item, acquisition):
        self.icon_path = "resources/acquisition.png"
        super(AcquisitionItem, self).__init__(session_item, acquisition)
        self.has_analyses = True
        self.acquisition = self.container


class AnalysisItem(ContainerItem):
    def __init__(self, parent_item, analysis):
        self.icon_path = "resources/analysis.png"
        super(AnalysisItem, self).__init__(parent_item, analysis)


class FileItem(ContainerItem):
    def __init__(self, parent_item, file_obj):
        file_obj.label = file_obj.name
        self.parent_item = parent_item
        self.container = file_obj
        self.file = file_obj
        if self._is_cached():
            self.icon_path = "resources/file_cached.png"
        else:
            self.icon_path = "resources/file.png"
        super(FileItem, self).__init__(parent_item, file_obj)

    def _get_cache_path(self):

        file_parent = self.parent_item.parent().container
        file_path = Path(os.path.expanduser("~") + "/flywheelIO/")

        for par in ["group", "project", "subject", "session", "acquisition"]:
            if file_parent.parents[par]:
                file_path /= file_parent.parents[par]
        file_path /= file_parent.id
        file_path /= self.container.id
        file_path /= self.container.name
        return file_path

    def _is_cached(self):
        return self._get_cache_path().exists()

    def _add_to_cache(self):
        file_path = self._get_cache_path()
        file_parent = self.parent_item.parent().container
        if not file_path.exists():
            if not file_path.parents[0].exists():
                os.makedirs(file_path.parents[0])
            file_parent.download_file(self.file.name, str(file_path))
            self.icon_path = "resources/file_cached.png"
            self._set_icon()
        return file_path
