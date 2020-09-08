# Development Notes

These are notes to assist in developing and maintaining the `Gear-Building GUI` in the absence of the original developer.

This will not be a complete introduction to GUI programming in Python or the myriad of other options to do so (Pyside, tktl, etc.). This document aims, instead, to quickly direct the developer/maintainer to resources that most readly facilitate that development.

## PyQt5

The `requirements.txt` of this repository contains the version of tools that this application is built upon. However, installation of the GUI Designer (**QT Designer**) is not included in these resources for Mac OS X.

### PyQt5 Designer

Multiple resources exist for installing the PyQt5 Designer on various platforms:

* linux: https://gist.github.com/ujjwal96/1dcd57542bdaf3c9d1b0dd526ccd44ff
* os x: https://stackoverflow.com/questions/46542326/installing-pyqt5-incl-qt-designer-on-macos-sierra
* windows: https://build-system.fman.io/qt-designer-download

### Simple Example

With the a PyQt5 Form designed and ready for execution, it is important to have the functional elements perform actions.  This is going to occur from "binding" events and signals to the functions that will perform the desired behavior.

```
cbo_type.currentIndexChanged.connect(config_type_changed)
```

The above code connects the `currentIndexChanged` event of the combo box `cbo_type` to a function `config_type_changed`.

## Code Structure

The project is divided into various sections to assist with ease of use.

### Top-Level

On the top-level, there is the `fw_app_launcher.py`. This is contains the central application object and reference to the main form.  It is intended to be a brief reference to the three groups of related functionality.  These three groups are: The tree representation of the Flywheel Container Hierarchy, the list of available applications to view data in, and the local analyses that we are saving data to.

As with the other form components, the `.ui` file that defines the form and all of the tabs resides in `./resources/`. We will revisit this later.

### resources

The `./resources` directory contains all of the functionality and resources for the gear components. This includes images for the container tree and forms (.ui) for rendering.

### management

The `./management` directory contains the python files that are responsible for managing each of class of functionality.

## TODOs:
- [ ] Move "Node ID" functionality to a context menu item in the TreeManagement class
- [ ] Flywheel logo and the instance they are logged into
- [ ] Recursively cache selected acquisitions.
- [ ] File download progress bar.
- [ ] BrainLife Example: https://youtu.be/H21eKZDJYxg?t=45
- [ ] Analyses need to be associated with an instance...regardless of their user permissions.