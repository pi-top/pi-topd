=======================
pi-topd (pi-top daemon)
=======================

Daemon for managing pi-top functionality by managing the pi-top hub connection.

--------------------
Build Status: Latest
--------------------

.. image:: https://img.shields.io/github/workflow/status/pi-top/pi-topd/Test%20and%20Build%20Packages%20on%20All%20Commits
   :alt: GitHub Workflow Status

.. image:: https://img.shields.io/github/v/tag/pi-top/pi-topd
    :alt: GitHub tag (latest by date)

.. image:: https://img.shields.io/github/v/release/pi-top/pi-topd
    :alt: GitHub release (latest by date)

.. https://img.shields.io/codecov/c/gh/pi-top/pi-topd?token=hfbgB9Got4
..   :alt: Codecov

-----
About
-----

This application runs as a background process in order to receive state/event information from pi-top hardware and manage the system configuration in order to provide plug-and-play functionality. It also provides an interface for getting information from the hub without requiring any knowledge of the hub's internal register interface.

`pi-topd` is included out-of-the-box with pi-topOS.

Ensure that you keep your system up-to-date to enjoy the latest features and bug fixes.

This is a Python 3 application that is managed by a systemd service, configured to automatically run on startup and restart during software updates.

------------
Installation
------------

`pi-topd` is installed out of the box with pi-topOS, which is available from
pi-top.com_. To install on Raspberry Pi OS or other operating systems, check out the `Using pi-top Hardware with Raspberry Pi OS`_ page on the pi-top knowledge base.

.. _pi-top.com: https://www.pi-top.com/products/os/

.. _Using pi-top Hardware with Raspberry Pi OS: https://knowledgebase.pi-top.com/knowledge/pi-top-and-raspberry-pi-os

----------------
More Information
----------------

Please refer to the `More Info`_ documentation in this repository
for more information about the application.

.. _More Info: https://github.com/pi-top/pi-topd/blob/master/docs/more-info.md

------------
Contributing
------------

Please refer to the `Contributing`_ document in this repository
for information on contributing to the project.

.. _Contributing: https://github.com/pi-top/pi-topd/blob/master/.github/CONTRIBUTING.md

See the `contributors page`_ on GitHub for more info on contributors.

.. _contributors page: https://github.com/pi-top/pitop/graphs/contributors
